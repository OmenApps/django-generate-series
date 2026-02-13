"""The core functionality for generating series in Django."""

import logging
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from typing import List, Optional, Set, Tuple, Type, Union

import django
from django.contrib.postgres import fields as pg_models
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import F
from django.db.models.sql import Query
from django.utils.module_loading import import_string
from django.utils.timezone import datetime as datetimetz

from django_generate_series.app_settings import (
    DGS_DEFAULT_AUTO_FIELD,
    DGS_DEFAULT_AUTO_FIELD_DEFAULT_CALLABLE,
)
from django_generate_series.exceptions import (
    InvalidIntervalUnit,
    InvalidStepValue,
    ModelFieldNotSupported,
)
from django_generate_series.type_checking import (
    INTERVAL_UNITS,
    get_output_field_class,
    get_type_checking_dict,
    get_value_field_class,
    is_range_field,
    is_supported_field,
)

logger = logging.getLogger(__name__)


class AbstractBaseSeriesModel(models.Model):
    """Exists only to ensure correct model subclasses are passed to SeriesQueryGenerator."""

    class Meta:
        """Meta class for the abstract model."""

        abstract = True


class SeriesQueryValidator:
    """Class to validate the input parameters for generating series.

    Takes a SeriesQueryGenerator instance and validates the input parameters.
    """

    def __init__(self, series_query_generator: "SeriesQueryGenerator"):
        self.series_query_generator = series_query_generator

    def validate(self):
        """Validate the input parameters for generating series."""

        self._validate_range()

        self._validate_param_type("start", self.series_query_generator.type_checking_dict["start_type"])
        self._validate_param_type("stop", self.series_query_generator.type_checking_dict["stop_type"])

        if self.series_query_generator.step:
            self._validate_param_type("step", self.series_query_generator.type_checking_dict["step_type"])

    def _validate_range(self):
        """Validate the start and stop values based on the field type."""
        if self.series_query_generator.start > self.series_query_generator.stop:
            raise ValueError("Start value must be smaller or equal to stop value")

        if not type(self.series_query_generator.start) is type(self.series_query_generator.stop):
            raise ValueError("Start and stop values must be of the same type")

    def _validate_param_type(self, param_name, expected_types):
        """Validate the type of the input parameters."""
        param_value = getattr(self.series_query_generator, param_name)
        if not any(isinstance(param_value, t) for t in expected_types):
            raise ValueError(
                f"{param_name.capitalize()} type of {expected_types} expected, but received type {type(param_value)}"
            )


class SeriesQueryGenerator:
    """Class to produce the raw SQL query for generating series."""

    def __init__(
        self,
        start,
        stop,
        step,
        span,
        include_id,
        queryset,
        iterable,
        model: AbstractBaseSeriesModel = None,
    ):
        self.start = start
        self.stop = stop
        self.step = step
        self.span = span
        self.include_id = include_id
        self.queryset = queryset
        self.iterable = list(iterable) if iterable else None

        self.term_type = type(model._meta.get_field("term"))
        self.type_checking_dict = get_type_checking_dict(self.term_type)

        self.field_type = self.type_checking_dict["field_type"]
        self.range = self.type_checking_dict["range"]

        self.validator = SeriesQueryValidator(self)
        self.validator.validate()

        self.raw_query = self._generate_raw_query()

    def _generate_raw_query(self):
        """Generate the raw SQL query for the series."""
        query_template = self._get_query_template()

        if isinstance(self.queryset, models.QuerySet):
            query_template = self._get_queryset_cartesian_product_template(query_template)
        if hasattr(self.iterable, "__iter__"):
            query_template = self._get_iterable_cartesian_product_template(query_template)

        logger.debug("Generated raw query:\n%s", query_template)
        return query_template

    def _get_queryset_cartesian_product_template(self, base_query):
        """Generate the SQL for Cartesian product of series with input queryset."""
        # Get the name of the primary key field
        pk_field_name = self.queryset.model._meta.pk.name  # pylint: disable=W0212

        subquery = self.queryset.values_list(pk_field_name, flat=True).query
        return f"""
            WITH series AS (
                {base_query}
            ),
            queryset_pks AS (
                {subquery}
            )
            SELECT series.term, queryset_pks.{pk_field_name} as value
            FROM series, queryset_pks
        """

    def _get_iterable_cartesian_product_template(self, base_query):
        """Generate the SQL for Cartesian product of series with input iterable."""
        return f"""
            WITH series AS (
                {base_query}
            ),
            iterable AS (
                SELECT UNNEST(%s) AS value
            )
            SELECT series.term, iterable.value
            FROM series, iterable
        """

    def _get_query_template(self):
        """Get the appropriate query template based on the field type."""
        templates = {
            pg_models.DateTimeRangeField: self._get_datetime_range_template(),
            pg_models.DateRangeField: self._get_date_range_template(),
            pg_models.DecimalRangeField: self._get_decimal_range_template(),
            pg_models.BigIntegerRangeField: self._get_biginteger_range_template(),
            pg_models.IntegerRangeField: self._get_integer_range_template(),
            models.DateTimeField: self._get_datetime_template(),
            models.DateField: self._get_date_template(),
            models.DecimalField: self._get_generic_template(),
            models.BigIntegerField: self._get_generic_template(),
            models.IntegerField: self._get_generic_template(),
        }
        return templates[self.field_type]

    def _get_datetime_range_template(self):
        """Get the template for generating a range of datetime values."""
        if self.include_id:
            return """
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
        return """
            --- %s
            SELECT tstzrange((lag(a) OVER()), a, '[)') AS term
                FROM generate_series(timestamptz %s, timestamptz %s, interval %s)
                AS a OFFSET 1
        """

    def _get_date_range_template(self):
        """Get the template for generating a range of date values."""
        if self.include_id:
            return """
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
        return """
            --- %s
            SELECT daterange((lag(a.n) OVER()), a.n, '[)') AS term
            FROM (
                SELECT generate_series(date %s, date %s, interval %s)::date
                AS n)
            AS a OFFSET 1
        """

    def _get_decimal_range_template(self):
        """Get the template for generating a range of decimal values."""
        if self.include_id:
            return """
                SELECT
                    row_number() over () as id,
                    "term"
                FROM
                    (
                        SELECT numrange(a, a + %s) AS term
                        FROM generate_series(%s, %s, %s) a
                    ) AS seriesquery
            """
        return """
            SELECT numrange(a, a + %s) AS term
            FROM generate_series(%s, %s, %s) a
        """

    def _get_biginteger_range_template(self):
        """Get the template for generating a range of biginteger values."""
        if self.include_id:
            return """
                SELECT
                    row_number() over () as id,
                    "term"
                FROM
                    (
                        SELECT int8range(a, a + %s)::int8range AS term
                        FROM generate_series(%s, %s, %s) a
                    ) AS subquery
            """
        return """
            SELECT int8range(a, a + %s)::int8range AS term
            FROM generate_series(%s, %s, %s) a
        """

    def _get_integer_range_template(self):
        """Get the template for generating a range of integer values."""
        if self.include_id:
            return """
                SELECT
                    row_number() over () as id,
                    "term"
                FROM
                    (
                        SELECT int4range(a, a + %s)::int4range AS term
                        FROM generate_series(%s, %s, %s) a
                    ) AS seriesquery
            """
        return """
            SELECT int4range(a, a + %s)::int4range AS term
            FROM generate_series(%s, %s, %s) a
        """

    def _get_datetime_template(self):
        """Get the template for generating a series of datetime values."""
        if self.include_id:
            return """
                --- %s
                SELECT
                    row_number() over () as id,
                    "term"
                FROM
                    (
                        SELECT generate_series(timestamptz %s, timestamptz %s, interval %s)::timestamptz term
                    ) AS seriesquery
            """
        return """
            --- %s
            SELECT generate_series(timestamptz %s, timestamptz %s, interval %s)::timestamptz term
        """

    def _get_date_template(self):
        """Get the template for generating a series of date values."""
        if self.include_id:
            return """
                --- %s
                SELECT
                    row_number() over () as id,
                    "term"
                FROM
                    (
                    SELECT
                        generate_series(date %s, date %s, interval %s)::date term
                    ) AS seriesquery
            """
        return """
            --- %s
            SELECT generate_series(date %s, date %s, interval %s)::date term
        """

    def _get_generic_template(self):
        """Get the template for generating a series of values."""
        if self.include_id:
            return """
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
        return """
            --- %s
            SELECT generate_series(%s, %s, %s) term
        """


class GenerateSeriesQuery(Query):
    """Custom query class for generating series."""

    def __init__(self, *args, _series_func=None, **kwargs):
        self._series_func = _series_func
        super().__init__(*args, **kwargs)

    def get_compiler(self, *args, **kwargs):
        """Customize the compiler behavior to include the series function."""
        compiler = super().get_compiler(*args, **kwargs)
        get_from_clause_method = compiler.get_from_clause

        def get_from_clause_wrapper(*args, **kwargs):
            """Wrap the get_from_clause method to include the series function."""
            source = self._series_func(self.model)

            result, params = get_from_clause_method(*args, **kwargs)
            wrapper = source.raw_query
            result[0] = f"({wrapper}) AS {tuple(compiler.query.alias_map)[0]}"

            if source.iterable:
                params = (source.span, source.start, source.stop, source.step or 1, source.iterable) + tuple(params)
            else:
                params = (source.span, source.start, source.stop, source.step or 1) + tuple(params)

            return result, params

        compiler.get_from_clause = get_from_clause_wrapper
        return compiler


class GenerateSeriesQuerySet(models.QuerySet):
    """Custom queryset for generating series."""

    def __init__(self, *args, query=None, _series_func=None, **kwargs):
        empty_query = query is None
        super().__init__(*args, query=query, **kwargs)
        if empty_query:
            self.query = GenerateSeriesQuery(
                self.model,
                _series_func=_series_func,
            )


class GenerateSeriesManager(models.Manager):
    """Custom manager for creating series."""

    def _generate_series(self, start, stop, step, span, include_id, queryset, iterable) -> models.QuerySet:
        """Generate a series of values based on the input parameters."""

        def series_func(cls):
            """Generate the series query."""
            model = self.model
            return SeriesQueryGenerator(
                model=model,
                start=start,
                stop=stop,
                step=step,
                span=span,
                include_id=include_id,
                queryset=queryset,
                iterable=iterable,
            )

        return GenerateSeriesQuerySet(self.model, using=self._db, _series_func=series_func)


class AbstractSeriesModel(AbstractBaseSeriesModel):
    """Abstract model for generating series."""

    objects = GenerateSeriesManager()

    class Meta:
        """Meta class for the abstract model."""

        abstract = True
        managed = False


def generate_series(
    *,
    start: Union[int, Decimal, date, datetime, datetimetz],
    stop: Union[int, Decimal, date, datetime, datetimetz],
    step: Optional[Union[int, Decimal, str]] = 1,
    span: Optional[int] = None,
    output_field: Optional[Type[models.Field]] = None,
    include_id: Optional[bool] = False,
    max_digits: Optional[Union[int, None]] = None,
    decimal_places: Optional[Union[int, None]] = None,
    default_bounds: Optional[Union[str, None]] = None,
    queryset: Optional[models.QuerySet] = None,
    iterable: Optional[Union[List, Tuple, Set, str]] = None,
) -> models.QuerySet:
    """Generate a series of values based on the input parameters.

    Args:
        start: The starting value of the series.
        stop: The ending value of the series.
        step: The increment between values in the series.
        span: The number of values to include in each range.
        output_field: The type of field to use in the model.
        include_id: Whether to include an ID field in the model.
        max_digits: The maximum number of digits to include in the model.
        decimal_places: The number of decimal places to include in the model.
        default_bounds: The default bounds for the range field.
        queryset: An optional QuerySet used to generate a Cartesian product with the series.
        iterable: An optional iterable used to generate a Cartesian product with the series.

    Returns:
        A queryset of the generated series with or without the Cartesian product.
    """

    # Determine the output field type if not provided
    output_field = output_field or get_output_field_class(start=start, span=span)

    # If the output_field is a range type, and `span` is not specified, set it to the same value as `step`
    if is_range_field(output_field):
        if span is None:
            span = step or 1

    if queryset is not None and iterable is not None:
        raise ValueError("Cannot provide both a queryset and an iterable for Cartesian product")

    # Ensure `iterable` is a tuple or convert it to a tuple to allow use of `@lru_cache` with `_make_model_class()`
    if iterable and not isinstance(iterable, tuple):
        iterable = tuple(iterable)

    model_class = _make_model_class(
        output_field, include_id, max_digits, decimal_places, default_bounds, queryset, iterable
    )

    return model_class.objects._generate_series(  # pylint: disable=W0212
        start=start,
        stop=stop,
        step=step,
        span=span,
        include_id=include_id,
        queryset=queryset,
        iterable=iterable,
    )


def _get_auto_field():
    """Get the default auto field for the dynamically generated model."""
    try:
        pk_class = import_string(DGS_DEFAULT_AUTO_FIELD)
    except ImportError as e:
        msg = (
            f"The settings refer to the module '{DGS_DEFAULT_AUTO_FIELD}' for the default auto field that could "
            f"not be imported."
        )
        raise ImproperlyConfigured(msg) from e

    return pk_class


def get_term_dict(
    output_field: Type[models.Field], include_id: bool, max_digits: int, decimal_places: int, default_bounds: str
) -> dict:
    """Generate the dictionary for the `term` model field based on the output field and other parameters."""
    term_dict = {}

    if include_id:
        term_dict["primary_key"] = False
    else:
        term_dict["primary_key"] = True

    if is_range_field(output_field) and django.VERSION >= (4, 2) and default_bounds is not None:
        # Versions of Django >= 4.2 include support for defining default range bounds for
        # Range fields other than those based on Integer, so use it if provided.
        term_dict["default_bounds"] = default_bounds

    elif issubclass(output_field, models.DecimalField):  # Check for DecimalField
        term_dict["max_digits"] = max_digits
        term_dict["decimal_places"] = decimal_places

    return term_dict


def get_value_dict(value_field_class: Type[models.Field], max_digits: int, decimal_places: int) -> dict:
    """Generate the dictionary for the `value` model field based on the queryset or iterable."""
    value_dict = {}

    if issubclass(value_field_class, models.DecimalField):
        value_dict["max_digits"] = max_digits
        value_dict["decimal_places"] = decimal_places

    return value_dict


@lru_cache(maxsize=128)
def _make_model_class(
    output_field: Type[models.Field],
    include_id: bool,
    max_digits: int,
    decimal_places: int,
    default_bounds: str,
    queryset: Optional[models.QuerySet] = None,
    iterable: Optional[Tuple] = None,
):
    """Create a model class for the series generation."""
    model_dict = {
        "Meta": type("Meta", (object,), {"managed": False}),
        "__module__": __name__,
    }

    if not is_supported_field(output_field):
        raise ModelFieldNotSupported("Invalid model field type used to generate series")

    # Limit default_bounds to valid string values
    if default_bounds not in ["[]", "()", "[)", "(]", None]:
        raise ValueError("Value of default_bounds must be one of: '[]', '()', '[)', '(]'")

    term_dict = get_term_dict(output_field, include_id, max_digits, decimal_places, default_bounds)

    if include_id:
        model_dict["id"] = _get_auto_field()(
            primary_key=True, editable=False, default=DGS_DEFAULT_AUTO_FIELD_DEFAULT_CALLABLE
        )
    model_dict["term"] = output_field(**term_dict)

    # Add the `value` field if queryset or iterable is provided
    if queryset or iterable:
        value_field = get_value_field_class(queryset, iterable)
        value_dict = get_value_dict(
            value_field,
            max_digits,
            decimal_places,
        )
        model_dict["value"] = value_field(**value_dict)

    class_name = _build_model_class_name(output_field, include_id, max_digits, decimal_places, default_bounds,
                                         queryset, iterable)

    return type(
        class_name,
        (AbstractSeriesModel,),
        model_dict,
    )


def _build_model_class_name(output_field, include_id, max_digits, decimal_places, default_bounds, queryset, iterable):
    """Build a unique model class name based on the parameters that affect model structure."""
    parts = [output_field.__name__, "Series"]
    if include_id:
        parts.append("Id")
    if max_digits is not None:
        parts.append(f"Md{max_digits}")
    if decimal_places is not None:
        parts.append(f"Dp{decimal_places}")
    if default_bounds is not None:
        bounds_str = default_bounds.replace("[", "I").replace("]", "I").replace("(", "E").replace(")", "E")
        parts.append(f"Bd{bounds_str}")
    if queryset is not None:
        parts.append("Qs")
    if iterable is not None:
        parts.append("It")
    return "".join(parts)
