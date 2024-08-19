"""Utility functions and constants for type checking and validation."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Tuple, Type, Union

from django.contrib.postgres import fields as pg_models
from django.db import models
from django.utils.timezone import datetime as datetimetz

from django_generate_series.exceptions import ModelFieldNotSupported

logger = logging.getLogger(__name__)


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


_SUPPORTED_RANGE_OUTPUT_FIELDS = (
    pg_models.BigIntegerRangeField,
    pg_models.IntegerRangeField,
    pg_models.DecimalRangeField,
    pg_models.DateTimeRangeField,
    pg_models.DateRangeField,
)

_SUPPORTED_OUTPUT_FIELDS = (
    models.IntegerField,
    models.BigIntegerField,
    models.DecimalField,
    models.DateField,
    models.DateTimeField,
    models.FloatField,
    *_SUPPORTED_RANGE_OUTPUT_FIELDS,
)

_FIELD_TYPE_STANDARD_DICT = {
    int: models.IntegerField,
    Decimal: models.DecimalField,
    date: models.DateField,
    datetime: models.DateTimeField,
    datetimetz: models.DateTimeField,
}

_FIELD_TYPE_RANGE_DICT = {
    int: pg_models.IntegerRangeField,
    Decimal: pg_models.DecimalRangeField,
    date: pg_models.DateRangeField,
    datetime: pg_models.DateTimeRangeField,
    datetimetz: pg_models.DateTimeRangeField,
}

_FIELD_TYPE_PK_DICT = {
    "AutoField": models.AutoField,
    "BigAutoField": models.BigAutoField,
    "SmallAutoField": models.SmallAutoField,
    "UUIDField": models.UUIDField,
}

_FIELD_TYPE_ITERABLE_DICT = {
    **_FIELD_TYPE_STANDARD_DICT,
    str: models.CharField,
    bool: models.BooleanField,
    float: models.FloatField,
    bytes: models.BinaryField,
    bytearray: models.BinaryField,
}


def _decimal_type_check():
    """Get the type checking dictionary for the Decimal field."""
    return {
        "start_type": [int, Decimal],
        "stop_type": [int, Decimal],
        "step_type": [int, Decimal],
        "span_type": None,
        "field_type": models.DecimalField,
        "range": False,
    }


def _decimal_range_type_check():
    """Get the type checking dictionary for the Decimal range field."""
    return {
        "start_type": [int, Decimal],
        "stop_type": [int, Decimal],
        "step_type": [int, Decimal],
        "span_type": [int, Decimal],
        "field_type": pg_models.DecimalRangeField,
        "range": True,
    }


def _datetime_type_check():
    """Get the type checking dictionary for the DateTime field."""
    return {
        "start_type": [datetime, datetimetz],
        "stop_type": [datetime, datetimetz],
        "step_type": [str],
        "span_type": None,
        "field_type": models.DateTimeField,
        "range": False,
    }


def _datetime_range_type_check():
    """Get the type checking dictionary for the DateTime range field."""
    return {
        "start_type": [datetime, datetimetz],
        "stop_type": [datetime, datetimetz],
        "step_type": [str],
        "span_type": None,
        "field_type": pg_models.DateTimeRangeField,
        "range": True,
    }


def _date_type_check():
    """Get the type checking dictionary for the Date field."""
    return {
        "start_type": [date],
        "stop_type": [date],
        "step_type": [str],
        "span_type": None,
        "field_type": models.DateField,
        "range": False,
    }


def _date_range_type_check():
    """Get the type checking dictionary for the Date range field."""
    return {
        "start_type": [date],
        "stop_type": [date],
        "step_type": [str],
        "span_type": None,
        "field_type": pg_models.DateRangeField,
        "range": True,
    }


def _integer_type_check(field_type):
    """Get the type checking dictionary for the Integer and BigInteger fields."""
    return {
        "start_type": [int],
        "stop_type": [int],
        "step_type": [int],
        "span_type": None,
        "field_type": field_type,
        "range": False,
    }


def _integer_range_type_check(field_type):
    """Get the type checking dictionary for the Integer and BigInteger range fields."""
    return {
        "start_type": [int],
        "stop_type": [int],
        "step_type": [int],
        "span_type": [int],
        "field_type": field_type,
        "range": True,
    }


# Type checking dictionary for the supported field types.
_TYPE_CHECKING_DICT = {
    models.DateTimeField: _datetime_type_check(),
    models.DateField: _date_type_check(),
    models.DecimalField: _decimal_type_check(),
    models.BigIntegerField: _integer_type_check(models.BigIntegerField),
    models.IntegerField: _integer_type_check(models.IntegerField),
    pg_models.DateTimeRangeField: _datetime_range_type_check(),
    pg_models.DateRangeField: _date_range_type_check(),
    pg_models.DecimalRangeField: _decimal_range_type_check(),
    pg_models.BigIntegerRangeField: _integer_range_type_check(pg_models.BigIntegerRangeField),
    pg_models.IntegerRangeField: _integer_range_type_check(pg_models.IntegerRangeField),
}


def get_output_field_class(
    start: Union[int, Decimal, datetime, date], span: Optional[Union[int, Decimal]] = None
) -> Type[models.Field]:
    """Get the output field based on the `start` and `span` values."""
    if span is not None:
        # If the span is not None, it is a range field.
        try:
            return _FIELD_TYPE_RANGE_DICT[type(start)]
        except KeyError as e:
            raise ModelFieldNotSupported(f"{type(start)} is not supported for range fields.") from e

    else:
        # If the span is None, it is a standard field.
        try:
            return _FIELD_TYPE_STANDARD_DICT[type(start)]
        except KeyError as e:
            raise ModelFieldNotSupported(f"{type(start)} is not supported for standard fields.") from e


def get_value_field_class(queryset: Optional[models.QuerySet], iterable: Optional[Tuple]) -> Type[models.Field]:
    """Get the value field based on the queryset or iterable."""
    if queryset is not None:
        value_field_type = queryset.model._meta.pk.get_internal_type()  # pylint: disable=W0212
        value_field_class = _FIELD_TYPE_PK_DICT.get(value_field_type)
    elif iterable is not None:
        value_field_type = type(iterable[0])
        value_field_class = _FIELD_TYPE_ITERABLE_DICT.get(value_field_type)

    if value_field_class is None:
        raise ModelFieldNotSupported(f"{value_field_type} is not supported for the value field.")

    return value_field_class


def get_type_checking_dict(term_type: Type[models.Field]) -> dict:
    """Get the type checking dictionary for the given term type."""
    try:
        return _TYPE_CHECKING_DICT[term_type]
    except KeyError as e:
        raise ModelFieldNotSupported("Invalid model field type used to generate series") from e


def is_range_field(field_type: Type[models.Field]) -> bool:
    """Check if the given field type is a range field."""
    return field_type in _SUPPORTED_RANGE_OUTPUT_FIELDS


def is_supported_field(field_type: Type[models.Field]) -> bool:
    """Check if the given field type is supported - either a standard or range field."""
    return field_type in _SUPPORTED_OUTPUT_FIELDS
