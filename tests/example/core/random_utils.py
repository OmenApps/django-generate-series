"""Utility functions for generating random datetime and date values.

These functions are useful for generating random datetime and date values for testing purposes.

Examples:
    To generate a random datetime within the next 10 days:
    >>> from tests.example.core.random_utils import get_random_datetime
    >>> random_datetime = get_random_datetime()

    To generate a random date within the next 10 days:
    >>> from tests.example.core.random_utils import get_random_date
    >>> random_date = get_random_date()

    To generate a random datetime range within the next 10 days:
    >>> from tests.example.core.random_utils import get_random_datetime_range
    >>> random_datetime_range = get_random_datetime_range()

    To generate a random date range within the next 10 days:
    >>> from tests.example.core.random_utils import get_random_date_range
    >>> random_date_range = get_random_date_range()

    To generate a random datetime within the next 10 days, starting from a specific date:
    >>> from tests.example.core.random_utils import get_random_datetime
    >>> from django.utils import timezone
    >>> random_datetime = get_random_datetime(min_date=timezone.now(), max_timedelta=timezone.timedelta(days=10))

    To generate a random date within the next 10 days, starting from a specific date:
    >>> from tests.example.core.random_utils import get_random_date
    >>> from django.utils import timezone
    >>> random_date = get_random_date(min_date=timezone.now(), max_timedelta=timezone.timedelta(days=10))
"""

import datetime
import random
from typing import Tuple

from django.utils import timezone


def get_random_datetime(
    min_date: timezone.datetime = timezone.now(), max_timedelta: timezone.timedelta = timezone.timedelta(days=10)
) -> timezone.datetime:
    """Given a min_date value and an optional timedelta, returns a random datetime within the resulting span."""

    # ToDo: Allow input of date or datetime objects

    max_date = min_date + max_timedelta

    if not min_date < max_date:
        raise ValueError("If a timedelta value is provided, it must be positive")

    time_between_dates = max_date - min_date
    seconds_between_dates = time_between_dates.total_seconds()
    random_number_of_seconds = random.randrange(int(seconds_between_dates))
    random_datetime = min_date + timezone.timedelta(seconds=random_number_of_seconds)
    return random_datetime


def get_random_date(*args, **kwargs) -> datetime.date:
    """Returns a random date within the resulting span.

    Takes same arguments as get_random_datetime.
    """
    return get_random_datetime(*args, **kwargs).date()


def get_random_datetime_range(
    *args, max_range_length_seconds: int = 60 * 60 * 24 * 14, **kwargs
) -> Tuple[timezone.datetime, timezone.datetime]:
    """Returns a datetime range tuple.

    This tuple has start_datetime between min_date and max_timedelta, and an end_datetime between start_datetime and
        max_range_length_seconds.

    Takes same arguments as get_random_datetime, with addition of max_range_length_seconds.
    """
    start_datetime = get_random_datetime(*args, **kwargs)
    end_datetime = start_datetime + timezone.timedelta(seconds=random.randrange(max_range_length_seconds))
    return (start_datetime, end_datetime)


def get_random_date_range(*args, **kwargs) -> Tuple[datetime.date, datetime.date]:
    """Returns a date range tuple.

    This tuple has start_datetime between min_date and max_timedelta, and an end_datetime between start_datetime and
        max_range_length_seconds.

    Takes same arguments as get_random_datetime_range.
    """
    start_datetime, end_datetime = get_random_datetime_range(*args, **kwargs)
    return (start_datetime.date(), end_datetime.date())
