import datetime
import decimal

from django.utils import timezone
from typing import List, Union


def _datetimes_using_end(start_datetime, step, end_datetime, strip_time):
    while start_datetime < end_datetime:
        if not strip_time:
            yield start_datetime
        else:
            yield start_datetime.date()
        start_datetime += step


def _datetimes_using_steps(start_datetime, step, num_steps, strip_time):
    while num_steps > 0:
        if not strip_time:
            yield start_datetime
        else:
            yield start_datetime.date()
        num_steps -= 1
        start_datetime += step


def _to_sequence_of_datetime_range(datetime_list: List[timezone.datetime], step: timezone.timedelta):
    return ((dt, dt + step) for dt in datetime_list)


def _to_sequence_of_date_range(date_list: List[timezone.datetime], step: timezone.timedelta):
    return ((dt, (dt + step)) for dt in date_list)


def get_datetime_sequence(
    start_datetime: timezone.datetime = timezone.now(),
    step: timezone.timedelta = timezone.timedelta(days=1),
    end_datetime: timezone.datetime = None,
    num_steps: int = 10,
    strip_time: bool = False,
):
    """
    Generates a sequential tuple of datimetimes from start_datetime to either end_datetime
      or over the number of steps, defaulting to 10 steps if neither is provided.

    start_datetime: defaults to timezone.now()
    step: defaults to 1 day if not provided
    end_datetime: timezone.datetime or None
    num_steps: defaults to 10 if not provided
    """

    if end_datetime is not None:
        # Using end_datetime
        if not start_datetime < end_datetime:
            raise ValueError("If an end_datetime is provided, it must be greater than start_datetime")
        datetimes = (dt for dt in _datetimes_using_end(start_datetime, step, end_datetime, strip_time))
    else:
        # Using num_steps
        if num_steps < 0:
            raise ValueError("If a num_steps value is provided, it must be positive")
        datetimes = (dt for dt in _datetimes_using_steps(start_datetime, step, num_steps, strip_time))

    return datetimes


def get_date_sequence(*args, **kwargs):
    """
    Generates a sequence of dates
        Takes same arguments as get_datetime_sequence
    """
    if not "strip_time" in locals():
        return get_datetime_sequence(*args, **kwargs, strip_time=True)
    return get_datetime_sequence(*args, **kwargs)


def get_datetime_range_sequence(*args, **kwargs):
    """
    Generates a sequence of datetime ranges
        Takes same arguments as get_datetime_sequence
    """
    if not "step" in locals():
        step = timezone.timedelta(days=1)
    return _to_sequence_of_datetime_range(get_datetime_sequence(*args, **kwargs), step)


def get_date_range_sequence(*args, **kwargs):
    """
    Generates a sequence of date ranges
        Takes same arguments as get_date_sequence
    """
    if not "step" in locals():
        step = timezone.timedelta(days=1)
    return _to_sequence_of_date_range(get_date_sequence(*args, **kwargs), step)


def _decimals_using_end(start, step, end):
    while start <= end:
        yield start
        start += step


def _decimals_using_steps(start, step, num_steps):
    while num_steps > 0:
        yield start
        num_steps -= 1
        start += step


def _to_sequence_of_decimal_range(decimal_list: List[decimal.Decimal], step: Union[decimal.Decimal, int]):
    return ((dt, (dt + step)) for dt in decimal_list)


def get_decimal_sequence(
    start: decimal.Decimal = decimal.Decimal("0.00"),
    step: Union[decimal.Decimal, int] = decimal.Decimal("1.00"),
    end: decimal.Decimal = None,
    num_steps: decimal.Decimal = decimal.Decimal("10.00"),
):
    """
    Generates a sequence of decimals
    """
    if end is not None:
        # Using end
        if not start < end:
            raise ValueError("If an end_value is provided, it must be greater than start")
        decimals = (dt for dt in _decimals_using_end(start, step, end))
    else:
        # Using num_steps
        if num_steps < 0:
            raise ValueError("If a num_steps value is provided, it must be positive")
        decimals = (dt for dt in _decimals_using_steps(start, step, num_steps))

    return decimals


def get_decimal_range_sequence(*args, **kwargs):
    """
    Generates a sequence of decimal ranges
        Takes same arguments as get_decimal_sequence
    """
    if not "step" in locals():
        step = decimal.Decimal("1.00")
    return _to_sequence_of_decimal_range(get_decimal_sequence(*args, **kwargs), step)
