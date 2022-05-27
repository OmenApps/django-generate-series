import datetime
import decimal

import pytest
from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField, DecimalRangeField, IntegerRangeField
from django.db import models
from django.db.models import Count, Exists, OuterRef, Subquery, Sum
from django.utils import timezone
from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange

from django_generate_series.models import generate_series
from tests.example.core.models import (
    ConcreteDateRangeTest,
    ConcreteDateTest,
    ConcreteDateTimeRangeTest,
    ConcreteDateTimeTest,
    ConcreteDecimalRangeTest,
    ConcreteDecimalTest,
    ConcreteIntegerRangeTest,
    ConcreteIntegerTest,
)
from tests.example.core.random_utils import (
    get_random_date,
    get_random_date_range,
    get_random_datetime,
    get_random_datetime_range,
)
from tests.example.core.sequence_utils import (
    get_date_range_sequence,
    get_date_sequence,
    get_datetime_range_sequence,
    get_datetime_sequence,
    get_decimal_range_sequence,
    get_decimal_sequence,
)


def test_random_utils():
    """Make sure random_utils.py functions work correctly"""

    # get_random_datetime()
    assert get_random_datetime()
    assert isinstance(get_random_datetime(), timezone.datetime)
    with pytest.raises(Exception) as error_msg:
        get_random_datetime(max_timedelta=timezone.timedelta(days=-100))
    assert "If a timedelta value is provided, it must be positive" in str(error_msg.value)

    # get_random_date()
    assert get_random_date()
    assert isinstance(get_random_date(), datetime.date)

    # get_random_datetime_range()
    assert get_random_datetime_range()
    assert len(get_random_datetime_range()) == 2
    assert all(
        [
            isinstance(get_random_datetime_range()[0], timezone.datetime),
            isinstance(get_random_datetime_range()[1], timezone.datetime),
        ]
    )

    # get_random_date_range()
    assert get_random_date_range()
    assert len(get_random_date_range()) == 2
    assert all(
        [
            isinstance(get_random_date_range()[0], datetime.date),
            isinstance(get_random_date_range()[1], datetime.date),
        ]
    )


def test_sequence_utils():
    """Make sure sequence_utils.py functions work correctly"""

    # get_datetime_sequence()
    assert get_datetime_sequence()
    dt_sequence = list(get_datetime_sequence())
    assert len(dt_sequence) == 10
    assert isinstance(dt_sequence[0], timezone.datetime)
    assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

    assert get_datetime_sequence(end_datetime=timezone.now() + timezone.timedelta(days=10))
    dt_sequence = list(get_datetime_sequence(end_datetime=timezone.now() + timezone.timedelta(days=9)))
    assert len(dt_sequence) == 10
    assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

    with pytest.raises(Exception) as error_msg:
        dt_sequence = list(get_datetime_sequence(end_datetime=timezone.now() - timezone.timedelta(days=9)))
    assert "If an end_datetime is provided, it must be greater than start_datetime" in str(error_msg.value)

    with pytest.raises(Exception) as error_msg:
        dt_sequence = list(get_datetime_sequence(num_steps=-10))
    assert "If a num_steps value is provided, it must be positive" in str(error_msg.value)

    # get_date_sequence()
    assert get_date_sequence()
    dt_sequence = list(get_date_sequence())
    assert len(dt_sequence) == 10
    assert isinstance(dt_sequence[0], datetime.date)
    assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

    assert get_date_sequence(end_datetime=timezone.now() + timezone.timedelta(days=10))
    dt_sequence = list(get_date_sequence(end_datetime=timezone.now() + timezone.timedelta(days=9)))
    assert len(dt_sequence) == 10
    assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

    # get_datetime_range_sequence()
    assert get_datetime_range_sequence()
    dt_sequence = list(get_datetime_range_sequence())
    assert len(dt_sequence) == 10
    assert isinstance(dt_sequence[0], tuple)
    assert len(dt_sequence[0]) == 2
    assert isinstance(dt_sequence[0][0], timezone.datetime)
    assert dt_sequence[9][0] - dt_sequence[0][0] == timezone.timedelta(days=9)
    assert dt_sequence[9][1] - dt_sequence[0][0] == timezone.timedelta(days=10)

    assert get_datetime_range_sequence(end_datetime=timezone.now() + timezone.timedelta(days=10))
    dt_sequence = list(get_datetime_range_sequence(end_datetime=timezone.now() + timezone.timedelta(days=9)))
    assert len(dt_sequence) == 10
    assert dt_sequence[9][0] - dt_sequence[0][0] == timezone.timedelta(days=9)
    assert dt_sequence[9][1] - dt_sequence[0][0] == timezone.timedelta(days=10)

    # get_date_range_sequence()
    assert get_date_range_sequence()
    dt_sequence = list(get_date_range_sequence())
    assert len(dt_sequence) == 10
    assert isinstance(dt_sequence[0], tuple)
    assert len(dt_sequence[0]) == 2
    assert isinstance(dt_sequence[0][0], datetime.date)
    assert dt_sequence[9][0] - dt_sequence[0][0] == timezone.timedelta(days=9)
    assert dt_sequence[9][1] - dt_sequence[0][0] == timezone.timedelta(days=10)

    assert get_date_range_sequence(end_datetime=timezone.now() + timezone.timedelta(days=10))
    dt_sequence = list(get_date_range_sequence(end_datetime=timezone.now() + timezone.timedelta(days=9)))
    assert len(dt_sequence) == 10
    assert dt_sequence[9][0] - dt_sequence[0][0] == timezone.timedelta(days=9)
    assert dt_sequence[9][1] - dt_sequence[0][0] == timezone.timedelta(days=10)

    # get_decimal_sequence()
    assert get_decimal_sequence()
    decimal_sequence = list(get_decimal_sequence())
    assert len(decimal_sequence) == 10
    assert isinstance(decimal_sequence[0], decimal.Decimal)
    assert decimal_sequence[9] - decimal_sequence[0] == decimal.Decimal("9.00")

    assert get_decimal_sequence(end=decimal.Decimal("9.00"))
    decimal_sequence = list(get_decimal_sequence(end=decimal.Decimal("9.00")))
    assert len(decimal_sequence) == 10
    assert decimal_sequence[9] - decimal_sequence[0] == decimal.Decimal("9.00")

    # get_decimal_range_sequence()
    assert get_decimal_range_sequence()
    decimal_sequence = list(get_decimal_range_sequence())
    assert len(decimal_sequence) == 10
    assert isinstance(decimal_sequence[0], tuple)
    assert len(decimal_sequence[0]) == 2
    assert isinstance(decimal_sequence[0][0], decimal.Decimal)
    assert decimal_sequence[9][0] - decimal_sequence[0][0] == decimal.Decimal("9.00")
    assert decimal_sequence[9][1] - decimal_sequence[0][0] == decimal.Decimal("10.00")

    assert get_decimal_range_sequence(num_steps=10)
    decimal_sequence = list(get_decimal_range_sequence(num_steps=10))
    assert len(decimal_sequence) == 10
    assert decimal_sequence[9][0] - decimal_sequence[0][0] == decimal.Decimal("9.00")
    assert decimal_sequence[9][1] - decimal_sequence[0][0] == decimal.Decimal("10.00")

    with pytest.raises(Exception) as error_msg:
        decimal_sequence = list(get_decimal_range_sequence(end=decimal.Decimal("-10.00")))
    assert "If an end_value is provided, it must be greater than start" in str(error_msg.value)

    with pytest.raises(Exception) as error_msg:
        decimal_sequence = list(get_decimal_range_sequence(num_steps=decimal.Decimal("-10.00")))
    assert "If a num_steps value is provided, it must be positive" in str(error_msg.value)


@pytest.mark.django_db
def test_integer_model():
    """Make sure we can create and use Integer sequences"""

    # Create concrete instances
    for idx in range(0, 10):
        ConcreteIntegerTest.objects.create(some_field=idx)

    # Run through some variations
    assert generate_series(0, 9, output_field=models.BigIntegerField).count() == 10
    assert generate_series(0, 9, 2, output_field=models.BigIntegerField).count() == 5
    assert generate_series(1, 1, output_field=models.BigIntegerField).count() == 1
    assert generate_series(0, 9, 2, include_id=True, output_field=models.BigIntegerField).count() == 5
    assert generate_series(0, 9, 2, include_id=True, output_field=models.BigIntegerField).last().id == 5

    # Make sure we can create a QuerySet and perform basic operations
    integer_test = generate_series(0, 9, output_field=models.BigIntegerField)
    assert integer_test.count() == 10
    assert integer_test.first().term == 0
    assert integer_test.last().term == 9
    integer_test_sum = integer_test.aggregate(int_sum=Sum("term"))
    assert integer_test_sum["int_sum"] == 45

    # Check that we can query from the concrete model
    assert ConcreteIntegerTest.objects.filter(some_field__in=integer_test.values("term")).count() == 10
    assert ConcreteIntegerTest.objects.filter(some_field__in=Subquery(integer_test.values("term"))).count() == 10

    integer_test_values = integer_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteIntegerTest.objects.filter(some_field__in=Subquery(integer_test_values)).count() == 10

    subquery_test = (
        ConcreteIntegerTest.objects.all()
        .annotate(val=Subquery(integer_test_values, output_field=models.IntegerField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 10
    assert subquery_test.first().val == 0
    assert subquery_test.last().val == 9

    subquery_exists_test = ConcreteIntegerTest.objects.all().annotate(
        integer_test=Exists(integer_test.filter(term=OuterRef("some_field")))
    )
    assert subquery_exists_test.first().some_field == 0
    assert subquery_exists_test.last().some_field == 9

    subquery_exists_test2 = ConcreteIntegerTest.objects.all().annotate(integer_test=Exists(integer_test_values))
    assert subquery_exists_test2.first().some_field == 0
    assert subquery_exists_test2.last().some_field == 9

    # Check that we can query from the generate series model
    concrete_integer_test_values = ConcreteIntegerTest.objects.values("some_field")
    assert (
        generate_series(0, 9, output_field=models.BigIntegerField)
        .filter(term__in=concrete_integer_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(0, 9, output_field=models.BigIntegerField)
        .filter(term__in=Subquery(concrete_integer_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_decimal_model():
    """Make sure we can create and use Decimal sequences"""

    # Create concrete instances
    for idx in range(0, 10):
        ConcreteDecimalTest.objects.create(some_field=idx)

    # Run through some variations
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=models.DecimalField
        ).count()
        == 10
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("2.00"), output_field=models.DecimalField
        ).count()
        == 5
    )
    assert (
        generate_series(
            decimal.Decimal("1.00"), decimal.Decimal("1.00"), decimal.Decimal("1.00"), output_field=models.DecimalField
        ).count()
        == 1
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"),
            decimal.Decimal("9.00"),
            decimal.Decimal("2.00"),
            include_id=True,
            output_field=models.DecimalField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"),
            decimal.Decimal("9.00"),
            decimal.Decimal("2.00"),
            include_id=True,
            output_field=models.DecimalField,
        )
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    decimal_test = generate_series(
        decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=models.DecimalField
    )
    assert decimal_test.count() == 10
    assert decimal_test.first().term == decimal.Decimal("0.00")
    assert decimal_test.last().term == decimal.Decimal("9.00")
    decimal_test_sum = decimal_test.aggregate(int_sum=Sum("term"))
    assert decimal_test_sum["int_sum"] == decimal.Decimal("45.00")

    # Check that we can query from the concrete model
    assert ConcreteDecimalTest.objects.filter(some_field__in=decimal_test.values("term")).count() == 10
    assert ConcreteDecimalTest.objects.filter(some_field__in=Subquery(decimal_test.values("term"))).count() == 10

    decimal_test_values = decimal_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDecimalTest.objects.filter(some_field__in=Subquery(decimal_test_values)).count() == 10

    subquery_test = (
        ConcreteDecimalTest.objects.all()
        .annotate(val=Subquery(decimal_test_values, output_field=models.DecimalField()))
        .filter(val__isnull=False)
    )

    assert subquery_test.count() == 10
    assert subquery_test.first().val == decimal.Decimal("0.00")
    assert subquery_test.last().val == decimal.Decimal("9.00")

    subquery_exists_test = ConcreteDecimalTest.objects.all().annotate(
        decimal_test=Exists(decimal_test.filter(term=OuterRef("some_field")).values("term"))
    )
    assert subquery_exists_test.first().some_field == decimal.Decimal("0.00")
    assert subquery_exists_test.last().some_field == decimal.Decimal("9.00")

    subquery_exists_test2 = ConcreteDecimalTest.objects.all().annotate(decimal_test=Exists(decimal_test_values))
    assert subquery_exists_test2.first().some_field == decimal.Decimal("0.00")
    assert subquery_exists_test2.last().some_field == decimal.Decimal("9.00")

    # Check that we can query from the generate series model
    concrete_decimal_test_values = ConcreteDecimalTest.objects.values("some_field")
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=models.DecimalField
        )
        .filter(term__in=concrete_decimal_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=models.DecimalField
        )
        .filter(term__in=Subquery(concrete_decimal_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_date_model():
    """Make sure we can create and use Date sequences"""

    # Create concrete instances
    date_sequence = tuple(get_date_sequence())
    for idx in date_sequence:
        ConcreteDateTest.objects.create(some_field=idx)

    # Run through some variations
    assert generate_series(date_sequence[0], date_sequence[-1], "1 days", output_field=models.DateField).count() == 10
    assert generate_series(date_sequence[0], date_sequence[-1], "2 days", output_field=models.DateField).count() == 5
    assert generate_series(date_sequence[0], date_sequence[0], "1 days", output_field=models.DateField).count() == 1
    assert (
        generate_series(
            date_sequence[0], date_sequence[-1], "2 days", include_id=True, output_field=models.DateField
        ).count()
        == 5
    )
    assert (
        generate_series(date_sequence[0], date_sequence[-1], "2 days", include_id=True, output_field=models.DateField)
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    date_test = generate_series(date_sequence[0], date_sequence[-1], "1 days", output_field=models.DateField)
    assert date_test.count() == 10
    assert date_test.first().term == date_sequence[0]
    assert date_test.last().term == date_sequence[-1]
    date_test_sum = date_test.aggregate(int_sum=Count("term"))
    assert date_test_sum["int_sum"] == 10

    # Check that we can query from the concrete model
    assert ConcreteDateTest.objects.filter(some_field__in=date_test.values("term")).count() == 10
    assert ConcreteDateTest.objects.filter(some_field__in=Subquery(date_test.values("term"))).count() == 10

    date_test_values = date_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDateTest.objects.filter(some_field__in=Subquery(date_test_values)).count() == 10

    subquery_test = (
        ConcreteDateTest.objects.all()
        .annotate(val=Subquery(date_test_values, output_field=models.DateField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 10
    assert subquery_test.first().val == date_sequence[0]
    assert subquery_test.last().val == date_sequence[-1]

    subquery_exists_test = ConcreteDateTest.objects.all().annotate(
        date_test=Exists(date_test.filter(term=OuterRef("some_field")))
    )
    assert subquery_exists_test.first().some_field == date_sequence[0]
    assert subquery_exists_test.last().some_field == date_sequence[-1]

    subquery_exists_test2 = ConcreteDateTest.objects.all().annotate(date_test=Exists(date_test_values))
    assert subquery_exists_test2.first().some_field == date_sequence[0]
    assert subquery_exists_test2.last().some_field == date_sequence[-1]

    # Check that we can query from the generate series model
    concrete_date_test_values = ConcreteDateTest.objects.values("some_field")
    assert (
        generate_series(date_sequence[0], date_sequence[-1], "1 days", output_field=models.DateField)
        .filter(term__in=concrete_date_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(date_sequence[0], date_sequence[-1], "1 days", output_field=models.DateField)
        .filter(term__in=Subquery(concrete_date_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_datetime_model():
    """Make sure we can create and use DateTime sequences"""

    # Create concrete instances
    datetime_sequence = tuple(get_datetime_sequence())
    print(datetime_sequence)

    for idx in datetime_sequence:
        ConcreteDateTimeTest.objects.create(some_field=idx)

    # Run through some variations
    assert (
        generate_series(
            datetime_sequence[0], datetime_sequence[-1], "1 days", output_field=models.DateTimeField
        ).count()
        == 10
    )
    assert (
        generate_series(
            datetime_sequence[0], datetime_sequence[-1], "2 days", output_field=models.DateTimeField
        ).count()
        == 5
    )
    assert (
        generate_series(
            datetime_sequence[0], datetime_sequence[0], "1 days", output_field=models.DateTimeField
        ).count()
        == 1
    )
    assert (
        generate_series(
            datetime_sequence[0], datetime_sequence[-1], "2 days", include_id=True, output_field=models.DateTimeField
        ).count()
        == 5
    )
    assert (
        generate_series(
            datetime_sequence[0], datetime_sequence[-1], "2 days", include_id=True, output_field=models.DateTimeField
        )
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    datetime_test = generate_series(
        datetime_sequence[0], datetime_sequence[-1], "1 days", output_field=models.DateTimeField
    )
    assert datetime_test.count() == 10
    assert datetime_test.first().term == datetime_sequence[0]
    assert datetime_test.last().term == datetime_sequence[-1]
    datetime_test_sum = datetime_test.aggregate(int_sum=Count("term"))
    assert datetime_test_sum["int_sum"] == 10

    # Check that we can query from the concrete model
    assert ConcreteDateTimeTest.objects.filter(some_field__in=datetime_test.values("term")).count() == 10
    assert ConcreteDateTimeTest.objects.filter(some_field__in=Subquery(datetime_test.values("term"))).count() == 10

    datetime_test_values = datetime_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDateTimeTest.objects.filter(some_field__in=Subquery(datetime_test_values)).count() == 10

    subquery_test = (
        ConcreteDateTimeTest.objects.all()
        .annotate(val=Subquery(datetime_test_values, output_field=models.DateTimeField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 10
    assert subquery_test.first().val == datetime_sequence[0]
    assert subquery_test.last().val == datetime_sequence[-1]

    subquery_exists_test = ConcreteDateTimeTest.objects.all().annotate(
        datetime_test=Exists(datetime_test.filter(term=OuterRef("some_field")))
    )
    assert subquery_exists_test.first().some_field == datetime_sequence[0]
    assert subquery_exists_test.last().some_field == datetime_sequence[-1]

    subquery_exists_test2 = ConcreteDateTimeTest.objects.all().annotate(datetime_test=Exists(datetime_test_values))
    assert subquery_exists_test2.first().some_field == datetime_sequence[0]
    assert subquery_exists_test2.last().some_field == datetime_sequence[-1]

    # Check that we can query from the generate series model
    concrete_datetime_test_values = ConcreteDateTimeTest.objects.values("some_field")
    assert (
        generate_series(datetime_sequence[0], datetime_sequence[-1], "1 days", output_field=models.DateTimeField)
        .filter(term__in=concrete_datetime_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(datetime_sequence[0], datetime_sequence[-1], "1 days", output_field=models.DateTimeField)
        .filter(term__in=Subquery(concrete_datetime_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_integer_range_model():
    """Make sure we can create and use Integer Range sequences"""

    # Create concrete instances
    integer_range_sequence = tuple(NumericRange(idx, idx + 1, "[)") for idx in range(0, 10))
    for item in integer_range_sequence:
        x = ConcreteIntegerRangeTest.objects.create(some_field=item)

    # Run through some variations
    assert generate_series(0, 9, output_field=IntegerRangeField).count() == 10
    assert generate_series(0, 9, 2, output_field=IntegerRangeField).count() == 5
    assert generate_series(1, 1, output_field=IntegerRangeField).count() == 1
    assert generate_series(0, 9, 2, include_id=True, output_field=IntegerRangeField).count() == 5
    assert generate_series(0, 9, 2, include_id=True, output_field=IntegerRangeField).last().id == 5

    # Make sure we can create a QuerySet and perform basic operations
    integer_range_test = generate_series(0, 9, output_field=IntegerRangeField)

    integer_range_test.first().term
    assert integer_range_test.count() == 10

    for item in integer_range_test:
        print(item.term)

    assert integer_range_test.first().term == integer_range_sequence[0]
    assert integer_range_test.get(term__overlap=(0, 1)) == integer_range_test.first()
    assert integer_range_test.first().term == NumericRange(0, 1, "[)")
    assert integer_range_test.last().term == integer_range_sequence[-1]

    integer_range_test_sum = integer_range_test.aggregate(int_sum=Count("term"))
    assert integer_range_test_sum["int_sum"] == 10

    assert integer_range_test.filter(term__contains=NumericRange(1, 2)).count() == 1

    # Check that we can query from the concrete model
    assert ConcreteIntegerRangeTest.objects.filter(some_field__in=integer_range_test.values("term")).count() == 10
    assert (
        ConcreteIntegerRangeTest.objects.filter(some_field__in=Subquery(integer_range_test.values("term"))).count()
        == 10
    )

    integer_range_test_values = integer_range_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteIntegerRangeTest.objects.filter(some_field__in=Subquery(integer_range_test_values)).count() == 10

    subquery_test = (
        ConcreteIntegerRangeTest.objects.all()
        .annotate(val=Subquery(integer_range_test_values, output_field=IntegerRangeField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 10
    assert subquery_test.first().val == integer_range_sequence[0]
    assert subquery_test.last().val == integer_range_sequence[-1]

    subquery_exists_test = ConcreteIntegerRangeTest.objects.all().annotate(
        integer_range_test=Exists(integer_range_test.filter(term=OuterRef("some_field")))
    )

    assert subquery_exists_test.first().some_field.lower == 0
    assert subquery_exists_test.first().some_field.upper == 1
    assert subquery_exists_test.last().some_field.lower == 9
    assert subquery_exists_test.last().some_field.upper == 10

    subquery_exists_test2 = ConcreteIntegerRangeTest.objects.all().annotate(
        integer_range_test=Exists(integer_range_test_values)
    )
    assert subquery_exists_test2.first().some_field == integer_range_sequence[0]
    assert subquery_exists_test2.last().some_field == integer_range_sequence[-1]

    # # Check that we can query from the generate series model
    concrete_integer_range_test_values = ConcreteIntegerRangeTest.objects.values("some_field")
    assert (
        generate_series(0, 9, output_field=IntegerRangeField)
        .filter(term__in=concrete_integer_range_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(0, 9, output_field=IntegerRangeField)
        .filter(term__in=Subquery(concrete_integer_range_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_decimal_range_model():
    """Make sure we can create and use Decimal Range sequences"""

    # Create concrete instances
    decimal_range_sequence = tuple(
        NumericRange(decimal.Decimal(idx), decimal.Decimal(idx + 1), "[)") for idx in range(0, 10)
    )

    for item in decimal_range_sequence:
        ConcreteDecimalRangeTest.objects.create(some_field=item)

    # Run through some variations
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=DecimalRangeField
        ).count()
        == 10
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("2.00"), output_field=DecimalRangeField
        ).count()
        == 5
    )
    assert (
        generate_series(
            decimal.Decimal("1.00"), decimal.Decimal("1.00"), decimal.Decimal("1.00"), output_field=DecimalRangeField
        ).count()
        == 1
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"),
            decimal.Decimal("9.00"),
            decimal.Decimal("2.00"),
            include_id=True,
            output_field=DecimalRangeField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"),
            decimal.Decimal("9.00"),
            decimal.Decimal("2.00"),
            include_id=True,
            output_field=DecimalRangeField,
        )
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    decimal_range_test = generate_series(
        decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=DecimalRangeField
    )
    assert decimal_range_test.count() == 10
    assert decimal_range_test.first().term == decimal_range_sequence[0]
    assert decimal_range_test.last().term == decimal_range_sequence[-1]
    decimal_range_test_sum = decimal_range_test.aggregate(int_sum=Count("term"))
    assert decimal_range_test_sum["int_sum"] == 10

    # Check that we can query from the concrete model
    assert ConcreteDecimalRangeTest.objects.filter(some_field__in=decimal_range_test.values("term")).count() == 10
    assert (
        ConcreteDecimalRangeTest.objects.filter(some_field__in=Subquery(decimal_range_test.values("term"))).count()
        == 10
    )

    decimal_range_test_values = decimal_range_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDecimalRangeTest.objects.filter(some_field__in=Subquery(decimal_range_test_values)).count() == 10

    subquery_test = (
        ConcreteDecimalRangeTest.objects.all()
        .annotate(val=Subquery(decimal_range_test_values, output_field=DecimalRangeField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 10
    assert subquery_test.first().val == decimal_range_sequence[0]
    assert subquery_test.last().val == decimal_range_sequence[-1]

    subquery_exists_test = ConcreteDecimalRangeTest.objects.all().annotate(
        decimal_range_test=Exists(decimal_range_test.filter(term=OuterRef("some_field")))
    )

    # !!! ToDo: Add this check to the other models!
    assert subquery_exists_test.first().some_field.lower == decimal.Decimal("0.0")
    assert subquery_exists_test.first().some_field.upper == decimal.Decimal("1.0")
    assert subquery_exists_test.last().some_field.lower == decimal.Decimal("9.0")
    assert subquery_exists_test.last().some_field.upper == decimal.Decimal("10.0")

    assert subquery_exists_test.first().some_field == decimal_range_sequence[0]
    assert subquery_exists_test.last().some_field == decimal_range_sequence[-1]

    subquery_exists_test2 = ConcreteDecimalRangeTest.objects.all().annotate(
        decimal_range_test=Exists(decimal_range_test_values)
    )

    # !!! ToDo: Add this check to the other models!
    assert subquery_exists_test2.first().some_field.lower == decimal.Decimal("0.0")
    assert subquery_exists_test2.first().some_field.upper == decimal.Decimal("1.0")
    assert subquery_exists_test2.last().some_field.lower == decimal.Decimal("9.0")
    assert subquery_exists_test2.last().some_field.upper == decimal.Decimal("10.0")

    assert subquery_exists_test2.first().some_field == decimal_range_sequence[0]
    assert subquery_exists_test2.last().some_field == decimal_range_sequence[-1]

    # Check that we can query from the generate series model
    concrete_decimal_range_test_values = ConcreteDecimalRangeTest.objects.values("some_field")
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=DecimalRangeField
        )
        .filter(term__in=concrete_decimal_range_test_values)
        .count()
        == 10
    )
    assert (
        generate_series(
            decimal.Decimal("0.00"), decimal.Decimal("9.00"), decimal.Decimal("1.00"), output_field=DecimalRangeField
        )
        .filter(term__in=Subquery(concrete_decimal_range_test_values))
        .count()
        == 10
    )


@pytest.mark.django_db
def test_date_range_model():
    """Make sure we can create and use Date Range sequences"""

    # Create concrete instances
    date_range_sequence = [
        DateRange(
            timezone.now().date() + timezone.timedelta(days=idx),
            (timezone.now().date() + timezone.timedelta(days=idx + 1)),
            "[)",
        )
        for idx in range(0, 9)
    ]

    for idx in date_range_sequence:
        ConcreteDateRangeTest.objects.create(some_field=idx)

    # Run through some variations
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=10),
            "1 days",
            output_field=DateRangeField,
        ).count()
        == 10
    )
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=10),
            "2 days",
            output_field=DateRangeField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date(),
            "1 days",
            output_field=DateRangeField,
        ).count()
        == 0
    )
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=10),
            "2 days",
            include_id=True,
            output_field=DateRangeField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=10),
            "2 days",
            include_id=True,
            output_field=DateRangeField,
        )
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    date_range_test = generate_series(
        timezone.now().date(),
        timezone.now().date() + timezone.timedelta(days=9),
        "1 days",
        output_field=DateRangeField,
    )
    assert date_range_test.count() == 9
    assert date_range_test.first().term == date_range_sequence[0]
    assert date_range_test.last().term == date_range_sequence[-1]
    date_range_test_sum = date_range_test.aggregate(int_sum=Count("term"))
    assert date_range_test_sum["int_sum"] == 9

    # Check that we can query from the concrete model
    assert ConcreteDateRangeTest.objects.filter(some_field__in=date_range_test.values("term")).count() == 9
    assert ConcreteDateRangeTest.objects.filter(some_field__in=Subquery(date_range_test.values("term"))).count() == 9

    date_range_test_values = date_range_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDateRangeTest.objects.filter(some_field__in=Subquery(date_range_test_values)).count() == 9

    subquery_test = (
        ConcreteDateRangeTest.objects.all()
        .annotate(val=Subquery(date_range_test_values, output_field=DateRangeField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 9
    assert subquery_test.first().val == date_range_sequence[0]
    assert subquery_test.last().val == date_range_sequence[-1]

    subquery_exists_test = ConcreteDateRangeTest.objects.all().annotate(
        date_range_test=Exists(date_range_test.filter(term=OuterRef("some_field")))
    )
    assert subquery_exists_test.first().some_field == date_range_sequence[0]
    assert subquery_exists_test.last().some_field == date_range_sequence[-1]

    subquery_exists_test2 = ConcreteDateRangeTest.objects.all().annotate(
        date_range_test=Exists(date_range_test_values)
    )
    assert subquery_exists_test2.first().some_field == date_range_sequence[0]
    assert subquery_exists_test2.last().some_field == date_range_sequence[-1]

    # Check that we can query from the generate series model
    concrete_date_range_test_values = ConcreteDateRangeTest.objects.values("some_field")
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=9),
            "1 days",
            output_field=DateRangeField,
        )
        .filter(term__in=concrete_date_range_test_values)
        .count()
        == 9
    )
    assert (
        generate_series(
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=9),
            "1 days",
            output_field=DateRangeField,
        )
        .filter(term__in=Subquery(concrete_date_range_test_values))
        .count()
        == 9
    )


@pytest.mark.django_db
def test_datetime_range_model():
    """Make sure we can create and use DateTime Range sequences"""

    # Create a range
    datetime_range_sequence = [
        DateTimeTZRange(
            (timezone.now() + timezone.timedelta(days=idx)).replace(hour=1, minute=2, second=3, microsecond=4),
            (timezone.now() + timezone.timedelta(days=idx + 1)).replace(hour=1, minute=2, second=3, microsecond=4),
            "[)",
        )
        for idx in range(0, 9)
    ]
    first_dt_in_range = datetime_range_sequence[0].lower
    last_dt_in_range = datetime_range_sequence[-1].upper

    # Create concrete instances
    for idx in datetime_range_sequence:
        x = ConcreteDateTimeRangeTest.objects.create(some_field=idx)

    # Run through some variations
    assert (
        generate_series(
            timezone.now(),
            timezone.now() + timezone.timedelta(days=10),
            "1 days",
            output_field=DateTimeRangeField,
        ).count()
        == 10
    )
    assert (
        generate_series(
            timezone.now(),
            timezone.now() + timezone.timedelta(days=10),
            "2 days",
            output_field=DateTimeRangeField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            timezone.now(),
            timezone.now(),
            "1 days",
            output_field=DateTimeRangeField,
        ).count()
        == 0
    )
    assert (
        generate_series(
            timezone.now(),
            timezone.now() + timezone.timedelta(days=10),
            "2 days",
            include_id=True,
            output_field=DateTimeRangeField,
        ).count()
        == 5
    )
    assert (
        generate_series(
            timezone.now(),
            timezone.now() + timezone.timedelta(days=10),
            "2 days",
            include_id=True,
            output_field=DateTimeRangeField,
        )
        .last()
        .id
        == 5
    )

    # Make sure we can create a QuerySet and perform basic operations
    datetime_range_test = generate_series(
        first_dt_in_range, last_dt_in_range, "1 days", output_field=DateTimeRangeField
    )

    assert datetime_range_test.count() == 9

    assert datetime_range_test.first().term == datetime_range_sequence[0]
    assert datetime_range_test.last().term == datetime_range_sequence[-1]
    date_range_test_sum = datetime_range_test.aggregate(int_sum=Count("term"))
    assert date_range_test_sum["int_sum"] == 9

    # Check that we can query from the concrete model

    assert ConcreteDateTimeRangeTest.objects.filter(some_field__in=datetime_range_test.values("term")).count() == 9
    assert (
        ConcreteDateTimeRangeTest.objects.filter(some_field__in=Subquery(datetime_range_test.values("term"))).count()
        == 9
    )

    datetime_range_test_values = datetime_range_test.filter(term=OuterRef("some_field")).values("term")
    assert ConcreteDateTimeRangeTest.objects.filter(some_field__in=Subquery(datetime_range_test_values)).count() == 9

    subquery_test = (
        ConcreteDateTimeRangeTest.objects.all()
        .annotate(val=Subquery(datetime_range_test_values, output_field=DateTimeRangeField()))
        .filter(val__isnull=False)
    )
    assert subquery_test.count() == 9
    assert subquery_test.first().val == datetime_range_sequence[0]
    assert subquery_test.last().val == datetime_range_sequence[-1]

    subquery_exists_test = ConcreteDateTimeRangeTest.objects.all().annotate(
        datetime_range_test=Exists(datetime_range_test.filter(term=OuterRef("some_field")))
    )
    assert subquery_exists_test.first().some_field.lower == datetime_range_sequence[0].lower
    assert subquery_exists_test.first().some_field.upper == datetime_range_sequence[0].upper
    assert subquery_exists_test.last().some_field.lower == datetime_range_sequence[-1].lower
    assert subquery_exists_test.last().some_field.upper == datetime_range_sequence[-1].upper

    subquery_exists_test2 = ConcreteDateTimeRangeTest.objects.all().annotate(
        datetime_range_test=Exists(datetime_range_test_values)
    )
    assert subquery_exists_test2.first().some_field.lower == datetime_range_sequence[0].lower
    assert subquery_exists_test2.first().some_field.upper == datetime_range_sequence[0].upper
    assert subquery_exists_test2.last().some_field.lower == datetime_range_sequence[-1].lower
    assert subquery_exists_test2.last().some_field.upper == datetime_range_sequence[-1].upper

    # Check that we can query from the generate series model
    concrete_datetime_range_test_values = ConcreteDateTimeRangeTest.objects.values("some_field")
    assert (
        generate_series(
            datetime_range_sequence[0].lower,
            datetime_range_sequence[-1].upper,
            "1 days",
            output_field=DateTimeRangeField,
        )
        .filter(term__in=concrete_datetime_range_test_values)
        .count()
        == 9
    )
    assert (
        generate_series(
            datetime_range_sequence[0].lower,
            datetime_range_sequence[-1].upper,
            "1 days",
            output_field=DateTimeRangeField,
        )
        .filter(term__in=Subquery(concrete_datetime_range_test_values))
        .count()
        == 9
    )
