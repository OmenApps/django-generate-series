# django-generate-series

Use Postgres' generate_series to create sequences with Django's ORM

https://django-generate-series.readthedocs.io/

## Goals

When using Postgres, the set-returning functions allow us to easily create sequences of numbers, dates, datetimes, etc. Unfortunately, this functionality is not currently available within the Django ORM.

This project makes it possible to create such sequences, which can then be used with Django QuerySets. For instance, assuming you have an Order model, you can create a set of sequential dates and then annotate each with the number of orders placed on that date. This will ensure you have no date gaps in the resulting QuerySet. To get the same effect without this package, additional post-processing of the QuerySet with Python would be required.

## Models

The package includes a `get_series_model` function from which you can create your own series-generating models in your project's models.py file. The field type passed into the function determines the resulting type of series that can be created.

Canonical examples for each supported series type:

```python
class IntegerTest(get_series_model(models.IntegerField)):
    # Creates a model for generating Integer series
    pass


class DecimalTest(get_series_model(models.DecimalField, max_digits=9, decimal_places=2)):
    # Creates a model for generating Decimal series
    pass


class DateTest(get_series_model(models.DateField)):
    # Creates a model for generating Date series
    pass


class DateTimeTest(get_series_model(models.DateTimeField)):
    # Creates a model for generating DateTime series
    pass
```

You can also create sequences of ranges.

```python
class IntegerRangeTest(get_series_model(IntegerRangeField)):
    # Creates a model for generating Integer range series
    pass


class DecimalRangeTest(get_series_model(DecimalRangeField)):
    # Creates a model for generating Decimal range series
    pass


class DateRangeTest(get_series_model(DateRangeField)):
    # Creates a model for generating Date range series
    pass


class DateTimeRangeTest(get_series_model(DateTimeRangeField)):
    # Creates a model for generating DateTime range series
    pass
```

*Note: See the docs and the example project in the tests directory for further examples of usage.*

## API

```python
# Create a BUNCH of sequential integers
integer_sequence_queryset = IntegerTest.objects.generate_series(
    [0, 100_000_000]
)

for item in integer_sequence_queryset:
    print(item.id, item.term)
```

Result:

    1 0
    2 1
    3 2
    4 3
    5 4
    6 5
    7 6
    8 7
    9 8
    10 9
    11 10
    ...

```python
# Create a sequence of dates from now until a year from now
now = timezone.now()
later = (now + timezone.timedelta(days=365))

date_sequence_queryset = DateTest.objects.generate_series(
    [now, later, "1 days"]
)

for item in date_sequence_queryset:
    print(item.id, item.term)
```

Result:

    1 2022-04-27 02:01:35.926057+00:00
    2 2022-04-28 02:01:35.926057+00:00
    3 2022-04-29 02:01:35.926057+00:00
    4 2022-04-30 02:01:35.926057+00:00
    5 2022-05-01 02:01:35.926057+00:00
    6 2022-05-02 02:01:35.926057+00:00
    7 2022-05-03 02:01:35.926057+00:00
    8 2022-05-04 02:01:35.926057+00:00
    9 2022-05-05 02:01:35.926057+00:00
    10 2022-05-06 02:01:35.926057+00:00
    11 2022-05-07 02:01:35.926057+00:00
    ...

## Terminology

Although this packages is named django-generate-series based on Postgres' [`generate_series` set-returning function](https://www.postgresql.org/docs/current/functions-srf.html), mathematically we are creating a [sequence](https://en.wikipedia.org/wiki/Sequence) rather than a [series](https://en.wikipedia.org/wiki/Series_(mathematics)).

- **sequence**: Formally, "a list of objects (or events) which have been ordered in a sequential fashion; such that each member either comes before, or after, every other member."

    In django-generate-series, we can generate sequences of integers, decimals, dates, datetimes, as well as the equivalent ranges of each of these types.

- **term**: The *n*th item in the sequence, where '*n*th' can be found using the id of the model instance.

    This is the name of the field in the model which contains the term value.
