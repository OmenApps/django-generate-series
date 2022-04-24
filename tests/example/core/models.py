from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField, DecimalRangeField, IntegerRangeField
from django.db import models

from django_generate_series.models import get_series_model


class IntegerTest(get_series_model(models.IntegerField)):
    pass


class DecimalTest(get_series_model(models.DecimalField, max_digits=9, decimal_places=2)):
    pass


class DateTest(get_series_model(models.DateField)):
    pass


class DateTimeTest(get_series_model(models.DateTimeField)):
    pass


class IntegerRangeTest(get_series_model(IntegerRangeField)):
    pass


class DecimalRangeTest(get_series_model(DecimalRangeField)):
    pass


class DateRangeTest(get_series_model(DateRangeField)):
    pass


class DateTimeRangeTest(get_series_model(DateTimeRangeField)):
    pass


class ConcreteIntegerTest(models.Model):
    some_field = models.IntegerField()


class ConcreteDecimalTest(models.Model):
    some_field = models.DecimalField(max_digits=9, decimal_places=2)


class ConcreteDateTest(models.Model):
    some_field = models.DateField()


class ConcreteDateTimeTest(models.Model):
    some_field = models.DateTimeField()


class ConcreteIntegerRangeTest(models.Model):
    some_field = IntegerRangeField()


class ConcreteDecimalRangeTest(models.Model):
    some_field = DecimalRangeField()


class ConcreteDateRangeTest(models.Model):
    some_field = DateRangeField()


class ConcreteDateTimeRangeTest(models.Model):
    some_field = DateTimeRangeField()


class SimpleOrder(models.Model):
    order_date = models.DateField()
    cost = models.IntegerField()


class Event(models.Model):
    event_datetime = models.DateTimeField()
    ticket_qty = models.IntegerField()
    false_field = models.BooleanField(default=False)
