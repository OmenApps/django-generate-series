"""Example models for testing."""

from django.contrib.postgres.fields import (
    DateRangeField,
    DateTimeRangeField,
    DecimalRangeField,
    IntegerRangeField,
)
from django.db import models


class ConcreteIntegerTest(models.Model):
    """A model with an IntegerField."""

    some_field = models.IntegerField()


class ConcreteDecimalTest(models.Model):
    """A model with a DecimalField."""

    some_field = models.DecimalField(max_digits=9, decimal_places=2)


class ConcreteDateTest(models.Model):
    """A model with a DateField."""

    some_field = models.DateField()


class ConcreteDateTimeTest(models.Model):
    """A model with a DateTimeField."""

    some_field = models.DateTimeField()


class ConcreteIntegerRangeTest(models.Model):
    """A model with an IntegerRangeField."""

    some_field = IntegerRangeField()


class ConcreteDecimalRangeTest(models.Model):
    """A model with a DecimalRangeField."""

    some_field = DecimalRangeField()


class ConcreteDateRangeTest(models.Model):
    """A model with a DateRangeField."""

    some_field = DateRangeField()


class ConcreteDateTimeRangeTest(models.Model):
    """A model with a DateTimeRangeField."""

    some_field = DateTimeRangeField()
