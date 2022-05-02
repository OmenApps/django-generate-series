from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField, DecimalRangeField, IntegerRangeField
from django.db import models


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
