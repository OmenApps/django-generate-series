"""
This module provides utility functions to generate sequences of datetimes and dates.

Examples:
    To generate a sequence of 10 datetimes starting from now:
    >>> from tests.example.core.sequence_utils import get_datetime_sequence
    >>> datetime_sequence = get_datetime_sequence()

    To generate a sequence of 10 dates starting from now:
    >>> from tests.example.core.sequence_utils import get_date_sequence
    >>> date_sequence = get_date_sequence()
"""

from django.utils import timezone


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


def get_datetime_sequence(
    start_datetime=None,
    step=None,
    end_datetime=None,
    num_steps=10,
    strip_time=False,
):
    """
    Generates a sequential tuple of datetimes from start_datetime to either end_datetime
      or over the number of steps, defaulting to 10 steps if neither is provided.

    start_datetime: defaults to timezone.now()
    step: defaults to 1 day if not provided
    end_datetime: timezone.datetime or None
    num_steps: defaults to 10 if not provided
    """
    if start_datetime is None:
        start_datetime = timezone.now()
    if step is None:
        step = timezone.timedelta(days=1)

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
    Generates a sequence of dates.
        Takes same arguments as get_datetime_sequence.
    """
    kwargs.setdefault("strip_time", True)
    return get_datetime_sequence(*args, **kwargs)
