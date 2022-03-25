import random
from django.utils import timezone


def get_random_datetime():
    start_date = timezone.datetime(2020, 1, 1)
    end_date = timezone.datetime(2020, 2, 1)
    time_between_dates = end_date - start_date
    seconds_between_dates = time_between_dates.total_seconds()
    random_number_of_seconds = random.randrange(seconds_between_dates)
    random_date = start_date + timezone.timedelta(seconds=random_number_of_seconds)
    return random_date


def get_random_date():
    return get_random_datetime().date()


def get_random_datetime_range():
    start_datetime = get_random_datetime()
    end_datetime = start_datetime + timezone.timedelta(seconds=random.randrange(60 * 60 * 14))
    return (start_datetime, end_datetime)


def get_random_date_range():
    start_datetime, end_datetime = get_random_datetime_range()
    return (start_datetime.date(), end_datetime.date())
