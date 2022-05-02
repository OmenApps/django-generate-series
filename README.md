# django-generate-series

Use Postgres' generate_series to create sequences with Django's ORM

https://django-generate-series.readthedocs.io/

## Goals

When using Postgres, the set-returning functions allow us to easily create sequences of numbers, dates, datetimes, etc. Unfortunately, this functionality is not currently available within the Django ORM.

This project makes it possible to create such sequences, which can then be used with Django QuerySets. For instance, assuming you have an Order model, you can create a set of sequential dates and then annotate each with the number of orders placed on that date. This will ensure you have no date gaps in the resulting QuerySet. To get the same effect without this package, additional post-processing of the QuerySet with Python would be required.

## Terminology

Although this packages is named django-generate-series based on Postgres' [`generate_series` set-returning function](https://www.postgresql.org/docs/current/functions-srf.html), mathematically we are creating a [sequence](https://en.wikipedia.org/wiki/Sequence) rather than a [series](https://en.wikipedia.org/wiki/Series_(mathematics)).

- **sequence**: Formally, "a list of objects (or events) which have been ordered in a sequential fashion; such that each member either comes before, or after, every other member."

    In django-generate-series, we can generate sequences of integers, decimals, dates, datetimes, as well as the equivalent ranges of each of these types.

- **term**: The *n*th item in the sequence, where '*n*th' can be found using the id of the model instance.

    This is the name of the field in the model which contains the term value.

## API

The package includes a `generate_series` function from which you can create your own series-generating QuerySets. The field type passed into the function as `output_field` determines the resulting type of series that can be created. (Thanks, [@adamchainz](https://twitter.com/adamchainz) for the format suggestion!)

### generate_series arguments

- ***start*** - The value at which the sequence should begin (required)
- ***stop*** - The value at which the sequence should end. For range types, this is the lower value of the final term (required)
- ***step*** - How many values to step from one term to the next. For range types, this is the step from the lower value of one term to the next. (required for non-integer types)
- ***span*** - For range types other than date and datetime, this determines the span of the lower value of a term and its upper value (optional, defaults to 1 if neeeded in the query)
- ***output_field*** - A django model field class, one of BigIntegerField, IntegerField, DecimalField, DateField, DateTimeField, BigIntegerRangeField, IntegerRangeField, DecimalRangeField, DateRangeField, or DateTimeRangeField. (required)
- ***include_id*** - If set to True, an auto-incrementing `id` field will be added to the QuerySet.
- ***max_digits*** - For decimal types, specifies the maximum digits
- ***decimal_places*** - For decimal types, specifies the number of decimal places
- ***default_bounds*** - In Django 4.1+, allows specifying bounds for list and tuple inputs. See [Django docs](https://docs.djangoproject.com/en/dev/releases/4.1/#django-contrib-postgres)

## Basic Examples

```python
# Create a bunch of sequential integers
integer_sequence_queryset = generate_series(
    0, 1000, output_field=models.IntegerField,
)

for item in integer_sequence_queryset:
    print(item.term)
```

Result:

    term
    ----
    0
    1
    2
    3
    4
    5
    6
    7
    8
    9
    10
    ...
    1000

```python
# Create a sequence of dates from now until a year from now
now = timezone.now().date()
later = (now + timezone.timedelta(days=365))

date_sequence_queryset = generate_series(
    now, later, "1 days", output_field=models.DateField,
)

for item in date_sequence_queryset:
    print(item.term)
```

Result:

    term
    ----
    2022-04-27
    2022-04-28
    2022-04-29
    2022-04-30
    2022-05-01
    2022-05-02
    2022-05-03
    ...
    2023-04-27

*Note: See [the docs](https://django-generate-series.readthedocs.io/en/latest/usage_examples.html) and the example project in the tests directory for further examples of usage.*

## Usage with partial

If you often need sequences of a given field type or with certain args, you can use [partial](https://docs.python.org/3/library/functools.html#functools.partial).

Example with default `include_id` and `output_field` values:

```python
from functools import partial

int_and_id_series = partial(generate_series, include_id=True, output_field=BigIntegerField)

qs = int_and_id_series(1, 100)
```
