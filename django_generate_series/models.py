import decimal
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Type, Union

import django
from django.contrib.postgres import fields as pg_models
from django.db import models
from django.db.models.sql import Query
from django.utils.timezone import datetime as datetimetz

from django_generate_series.exceptions import ModelFieldNotSupported

INTERVAL_UNITS = (
    "century",
    "centuries",
    "day",
    "days",
    "decade",
    "decades",
    "hour",
    "hours",
    "microsecond",
    "microseconds",
    "millennium",
    "millennia",
    "millenniums",
    "millisecond",
    "milliseconds",
    "minute",
    "minutes",
    "month",
    "months",
    "second",
    "seconds",
    "week",
    "weeks",
    "year",
    "years",
)


class FieldType(Enum):
    INTEGER = 1
    BIGINTEGER = 2
    DECIMAL = 3
    DATE = 4
    DATETIME = 5


class AbstractBaseSeriesModel(models.Model):
    """Exists only to ensure correct model subclasses are passed to FromRaw"""

    class Meta:
        abstract = True


class FromRaw:
    def __init__(
        self,
        start,
        stop,
        step=None,
        span=None,
        include_id=False,
        model: AbstractBaseSeriesModel = None,
    ):
        self.term = type(model._meta.get_field("term"))
        self.start = start
        self.stop = stop
        self.step = step
        self.span = span
        self.include_id = include_id
        self.range = False
        self.field_type = FieldType.INTEGER

        # Verify the input params match for the type of model field used

        # ToDo: Check span type

        if issubclass(self.term, (models.DecimalField, pg_models.DecimalRangeField)):
            self.check_params(
                start_type=[int, Decimal],
                stop_type=[int, Decimal],
                step_type=[int, Decimal],
            )
            self.field_type = FieldType.DECIMAL

        elif issubclass(self.term, (models.DateTimeField, pg_models.DateTimeRangeField)):
            self.check_params(
                start_type=[datetime, datetimetz],
                stop_type=[datetime, datetimetz],
                step_type=[str],
            )
            self.field_type = FieldType.DATETIME

        elif issubclass(self.term, (models.DateField, pg_models.DateRangeField)):
            self.check_params(
                start_type=[date],
                stop_type=[date],
                step_type=[str],
            )
            self.field_type = FieldType.DATE

        elif issubclass(
            self.term,
            (
                models.BigIntegerField,
                models.IntegerField,
                pg_models.BigIntegerRangeField,
                pg_models.IntegerRangeField,
            ),
        ):
            self.check_params(
                start_type=[int],
                stop_type=[int],
                step_type=[int],
            )

            if issubclass(self.term, (models.BigIntegerField, pg_models.BigIntegerRangeField)):
                self.field_type = FieldType.BIGINTEGER

        else:
            raise ModelFieldNotSupported("Invalid model field type used to generate series")

        if issubclass(
            self.term,
            (
                pg_models.BigIntegerRangeField,
                pg_models.IntegerRangeField,
                pg_models.DecimalRangeField,
                pg_models.DateRangeField,
                pg_models.DateTimeRangeField,
            ),
        ):
            self.range = True

        self.raw_query = f"({self.get_raw_query()})"

    def check_params(
        self,
        start_type: List[Union[Type[int], Type[decimal.Decimal], Type[date], Type[datetime], Type[datetimetz]]],
        stop_type: List[Union[Type[int], Type[decimal.Decimal], Type[date], Type[datetime], Type[datetimetz]]],
        step_type: List[Union[Type[int], Type[decimal.Decimal], Type[str]]],
    ):

        # Check that `start`, `stop`, and `step` are the correct type
        if not any(issubclass(type(self.start), item) for item in start_type):
            raise ValueError(f"Start type of {start_type} expected, but received type {type(self.start)}")
        if not any(issubclass(type(self.stop), item) for item in stop_type):
            raise ValueError(f"Stop type of {stop_type} expected, but received type {type(self.stop)}")
        if self.step is not None and not any(issubclass(type(self.step), item) for item in step_type):
            raise ValueError(f"Step type of {step_type} expected, but received type {type(self.step)}")

        # Check that stop is larger or equal to start
        if not self.start <= self.stop:
            raise ValueError(f"Start value must be smaller or equal to stop value")

        # Only numeric series can use just `start` & `stop`. Other types also need `step`
        if self.step is None and not isinstance(self.start, int):
            raise Exception(f"Step must be provided for non-integer series")

        # If step is a str, make sure it is formatted correctly
        #   Starting with a numeric value, then a space, and then a valid interval unit
        if isinstance(self.step, str):
            try:
                interval, interval_unit = self.step.split()
            except ValueError:
                raise Exception(
                    "Incorrect number of values for series step string. "
                    "Should be a numeric value, a space, and an interval type."
                )

            try:
                interval = float(interval)
            except ValueError:
                raise ValueError("Invalid interval value. Must be capable of being converted to a numeric type.")

            if not interval_unit in INTERVAL_UNITS:
                raise Exception("Invalid interval unit")

    def get_raw_query(self):
        if self.range:

            if self.field_type == FieldType.DATETIME:
                if self.include_id:
                    sql = """
                        --- %s
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                                SELECT tstzrange((lag(a) OVER()), a, '[)') AS term
                                FROM generate_series(timestamptz %s, timestamptz %s, interval %s)
                                AS a OFFSET 1
                            ) AS subquery
                    """
                else:
                    sql = """
                        --- %s
                        SELECT tstzrange((lag(a) OVER()), a, '[)') AS term
                            FROM generate_series(timestamptz %s, timestamptz %s, interval %s)
                            AS a OFFSET 1
                    """
            elif self.field_type == FieldType.DATE:
                if self.include_id:
                    sql = """
                        --- %s
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                                SELECT daterange((lag(a.n) OVER()), a.n, '[)') AS term
                                FROM (
                                    SELECT generate_series(date %s, date %s, interval %s)::date
                                    AS n)
                                AS a OFFSET 1
                            ) AS seriesquery
                    """
                else:
                    sql = """
                        --- %s
                        SELECT daterange((lag(a.n) OVER()), a.n, '[)') AS term
                        FROM (
                            SELECT generate_series(date %s, date %s, interval %s)::date
                            AS n)
                        AS a OFFSET 1
                    """
            elif self.field_type == FieldType.DECIMAL:
                if self.include_id:
                    sql = """
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                                SELECT numrange(a, a + %s) AS term
                                FROM generate_series(%s, %s, %s) a
                            ) AS seriesquery
                    """
                else:
                    sql = """
                        SELECT numrange(a, a + %s) AS term
	                        FROM generate_series(%s, %s, %s) a
                    """
            elif self.field_type == FieldType.BIGINTEGER:
                if self.include_id:
                    sql = """
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                                SELECT int8range(a, a + %s) AS term
                                FROM generate_series(%s, %s, %s) a
                            ) AS subquery
                    """
                else:
                    sql = """
                       SELECT int8range(a, a + %s) AS term
                        FROM generate_series(%s, %s, %s) a
                    """
            else:
                # ToDo: Instead of `a + 1`, we could make possible other options as well
                if self.include_id:
                    sql = """
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                                SELECT int4range(a, a + %s) AS term
                                FROM generate_series(%s, %s, %s) a
                            ) AS seriesquery
                    """
                else:
                    sql = """
                        SELECT int4range(a, a + %s) AS term
                        FROM generate_series(%s, %s, %s) a
                    """
        else:
            if self.field_type == FieldType.DATE:
                # Must specify this one, or defaults timestamptz rather than date
                if self.include_id:
                    sql = """
                        --- %s
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                            SELECT
                                generate_series(%s, %s, %s)::date term
                            ) AS seriesquery
                    """
                else:
                    sql = """
                        --- %s
                        SELECT generate_series(%s, %s, %s)::date term
                    """
            else:
                if self.include_id:
                    sql = """
                        --- %s
                        SELECT
                            row_number() over () as id,
                            "term"
                        FROM
                            (
                            SELECT
                                generate_series(%s, %s, %s) term
                            ) AS seriesquery
                    """
                else:
                    sql = """
                        --- %s
                        SELECT generate_series(%s, %s, %s) term
                    """

        return sql


class GenerateSeriesQuery(Query):
    def __init__(self, *args, _series_func=None, **kwargs):
        self._series_func = _series_func
        return super().__init__(*args, **kwargs)

    def get_compiler(self, *args, **kwargs):
        compiler = super().get_compiler(*args, **kwargs)
        get_from_clause_method = compiler.get_from_clause

        def get_from_clause_wrapper(*args, **kwargs):
            source = self._series_func(self.model)
            result, params = get_from_clause_method(*args, **kwargs)
            wrapper = source.raw_query
            result[0] = f"{wrapper} AS {tuple(compiler.query.alias_map)[0]}"
            params = (source.span, source.start, source.stop, source.step or 1) + tuple(params)

            return result, params

        compiler.get_from_clause = get_from_clause_wrapper
        return compiler


class GenerateSeriesQuerySet(models.QuerySet):
    def __init__(self, *args, query=None, _series_func=None, **kwargs):
        empty_query = query is None
        r = super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = GenerateSeriesQuery(
                self.model,
                _series_func=_series_func,
            )
        return r


class GenerateSeriesManager(models.Manager):
    """Custom manager for creating series"""

    def _generate_series(self, start, stop, step=None, span=None, include_id=False):

        # def series_func(cls, *args):
        def series_func(cls):
            model = self.model
            return FromRaw(model=model, start=start, stop=stop, step=step, span=span, include_id=include_id)

        return GenerateSeriesQuerySet(self.model, using=self._db, _series_func=series_func)


class AbstractSeriesModel(AbstractBaseSeriesModel):
    objects = GenerateSeriesManager()

    class Meta:
        abstract = True
        managed = False


def generate_series(
    start: Union[int, date, datetime, datetimetz],
    stop: Union[int, date, datetime, datetimetz],
    step: Optional[Union[int, str]] = None,
    span: Optional[int] = 1,
    *,
    output_field: Type[models.Field],
    include_id: Optional[bool] = False,
    max_digits: Optional[Union[int, None]] = None,
    decimal_places: Optional[Union[int, None]] = None,
    default_bounds: Optional[Union[str, None]] = None,
):
    model_class = _make_model_class(output_field, include_id, max_digits, decimal_places, default_bounds)
    return model_class.objects._generate_series(start, stop, step, span, include_id)


@lru_cache(maxsize=128)
def _make_model_class(output_field, include_id, max_digits, decimal_places, default_bounds):
    model_dict = {
        "Meta": type("Meta", (object,), {"managed": False}),
        "__module__": __name__,
    }
    term_dict = {}

    if not issubclass(
        output_field,
        (
            models.BigIntegerField,
            models.IntegerField,
            models.DecimalField,
            models.DateField,
            models.DateTimeField,
            pg_models.BigIntegerRangeField,
            pg_models.IntegerRangeField,
            pg_models.DecimalRangeField,
            pg_models.DateRangeField,
            pg_models.DateTimeRangeField,
        ),
    ):
        raise ModelFieldNotSupported("Invalid model field type used to generate series")

    # Limit default_bounds to valid string values
    if default_bounds not in ["[]", "()", "[)", "(]", None]:
        raise ValueError(f"Value of default_bounds must be one of: '[]', '()', '[)', '(]'")

    if include_id:
        model_dict["id"] = models.BigAutoField(primary_key=True)
    else:
        term_dict["primary_key"] = True

    if (
        issubclass(
            output_field,
            (
                pg_models.DecimalRangeField,
                pg_models.DateRangeField,
                pg_models.DateTimeRangeField,
            ),
        )
        and django.VERSION >= (4, 1)
        and default_bounds is not None
    ):
        # Versions of Django > 4.1 include support for defining default range bounds for
        #   Range fields other than those based on Integer, so use it if provided.
        term_dict["default_bounds"] = default_bounds

    elif issubclass(output_field, models.DecimalField):  # Do we need to check for DecimalRangeField as well?
        term_dict["max_digits"] = max_digits
        term_dict["decimal_places"] = decimal_places

    model_dict["term"] = output_field(**term_dict)

    return type(
        f"{output_field.__name__}Series",
        (AbstractSeriesModel,),
        model_dict,
    )
