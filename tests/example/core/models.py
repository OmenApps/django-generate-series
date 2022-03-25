from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField, IntegerRangeField
from django.db import models

from django_generate_series.models import get_series_model


class IntegerTest(get_series_model(models.IntegerField)):
    pass


class DateTest(get_series_model(models.DateField)):
    pass


class DateTimeTest(get_series_model(models.DateTimeField)):
    pass


class IntegerRangeTest(get_series_model(IntegerRangeField)):
    pass


class DateRangeTest(get_series_model(DateRangeField)):
    pass


class DateTimeRangeTest(get_series_model(DateTimeRangeField)):
    pass


class ConreteIntegerTest(models.Model):
    some_field = models.IntegerField()


class ConreteDateTest(models.Model):
    some_field = models.DateField()


class ConreteDateTimeTest(models.Model):
    some_field = models.DateTimeField()


class ConreteIntegerRangeTest(models.Model):
    some_field = IntegerRangeField()


class ConreteDateRangeTest(models.Model):
    some_field = DateRangeField()


class ConreteDateTimeRangeTest(models.Model):
    some_field = DateTimeRangeField()
