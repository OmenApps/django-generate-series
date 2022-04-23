# django-generate-series

## Goals

When using Postgres, the set-returning functions allow us to easily create sequences of numbers, dates, datetimes, etc. Unfortunately, this functionality is not currently available within the Django ORM.

This project makes it possible to create such sequences, which can then be used with Django QuerySets. For instance, assuming you have an Order model, you can create a set of sequential dates and then annotate each with the number of orders placed on that date. This will ensure you have no date gaps in the resulting QuerySet. To get the same effect without this package, additional post-processing of the QuerySet with Python would be required.

## API

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

*Note: See the example project in the tests directory for further examples of usage.*
