"""Tests for the core functionality of django-generate-series."""

import datetime
import decimal

import pytest
from django.contrib.postgres.fields import (
    BigIntegerRangeField,
    DateRangeField,
    DateTimeRangeField,
    DecimalRangeField,
    IntegerRangeField,
)
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import (
    AutoField,
    Count,
    Exists,
    OuterRef,
    Subquery,
    Sum,
    UUIDField,
)
from django.utils import timezone
from psycopg2.extras import DateRange, DateTimeTZRange, NumericRange

from django_generate_series.exceptions import ModelFieldNotSupported
from django_generate_series.models import (
    _get_auto_field,
    _make_model_class,
    generate_series,
    get_term_dict,
    get_value_dict,
)
from django_generate_series.type_checking import (
    get_output_field_class,
    get_type_checking_dict,
    get_value_field_class,
)
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


class TestRandomUtils:
    """Make sure random_utils.py functions work correctly."""

    def test_get_random_datetime(self):
        """Make sure we can generate a random datetime."""
        assert get_random_datetime()
        assert isinstance(get_random_datetime(), timezone.datetime)
        with pytest.raises(Exception) as error_msg:
            get_random_datetime(max_timedelta=timezone.timedelta(days=-100))
        assert "If a timedelta value is provided, it must be positive" in str(error_msg.value)

    def test_get_random_date(self):
        """Make sure we can generate a random date."""
        assert get_random_date()
        assert isinstance(get_random_date(), datetime.date)

    def test_get_random_datetime_range(self):
        """Make sure we can generate a random datetime range."""
        assert get_random_datetime_range()
        assert len(get_random_datetime_range()) == 2
        assert all(
            [
                isinstance(get_random_datetime_range()[0], timezone.datetime),
                isinstance(get_random_datetime_range()[1], timezone.datetime),
            ]
        )

    def test_get_random_date_range(self):
        """Make sure we can generate a random date range."""
        assert get_random_date_range()
        assert len(get_random_date_range()) == 2
        assert all(
            [
                isinstance(get_random_date_range()[0], datetime.date),
                isinstance(get_random_date_range()[1], datetime.date),
            ]
        )


class TestSequenceUtils:
    """Make sure sequence_utils.py functions work correctly."""

    def test_get_datetime_sequence(self):
        """Make sure we can generate a sequence of datetimes."""
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

    def test_get_date_sequence(self):
        """Make sure we can generate a sequence of dates."""
        assert get_date_sequence()
        dt_sequence = list(get_date_sequence())
        assert len(dt_sequence) == 10
        assert isinstance(dt_sequence[0], datetime.date)
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

        assert get_date_sequence(end_datetime=timezone.now() + timezone.timedelta(days=10))
        dt_sequence = list(get_date_sequence(end_datetime=timezone.now() + timezone.timedelta(days=9)))
        assert len(dt_sequence) == 10
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

    def test_get_datetime_range_sequence(self):
        """Make sure we can generate a sequence of datetime ranges."""
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

    def test_get_date_range_sequence(self):
        """Make sure we can generate a sequence of date ranges."""
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

    def test_get_decimal_sequence(self):
        """Make sure we can generate a sequence of decimals."""
        assert get_decimal_sequence()
        decimal_sequence = list(get_decimal_sequence())
        assert len(decimal_sequence) == 10
        assert isinstance(decimal_sequence[0], decimal.Decimal)
        assert decimal_sequence[9] - decimal_sequence[0] == decimal.Decimal("9.00")

        assert get_decimal_sequence(end=decimal.Decimal("9.00"))
        decimal_sequence = list(get_decimal_sequence(end=decimal.Decimal("9.00")))
        assert len(decimal_sequence) == 10
        assert decimal_sequence[9] - decimal_sequence[0] == decimal.Decimal("9.00")

    def test_get_decimal_range_sequence(self):
        """Make sure we can generate a sequence of decimal ranges."""
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
class TestIntegerModel:
    """Make sure we can create and use Integer sequences."""

    def test_bigintegerfield_variations(self):
        """Make sure we can create and use BigInteger sequences"""
        assert generate_series(start=0, stop=9, output_field=models.BigIntegerField).count() == 10

        assert generate_series(start=0, stop=9, step=2, output_field=models.BigIntegerField).count() == 5

        assert generate_series(start=1, stop=1, output_field=models.BigIntegerField).count() == 1

        assert (
            generate_series(start=0, stop=9, step=2, include_id=True, output_field=models.BigIntegerField).count() == 5
        )

        assert (
            generate_series(start=0, stop=9, step=2, include_id=True, output_field=models.BigIntegerField).last().id
            == 5
        )

    def test_bigintegerfield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        integer_test = generate_series(start=0, stop=9, output_field=models.BigIntegerField)
        assert integer_test.count() == 10
        assert integer_test.first().term == 0
        assert integer_test.last().term == 9
        integer_test_sum = integer_test.aggregate(int_sum=Sum("term"))
        assert integer_test_sum["int_sum"] == 45

        for idx in range(0, 10):
            ConcreteIntegerTest.objects.create(some_field=idx)

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
            generate_series(start=0, stop=9, output_field=models.BigIntegerField)
            .filter(term__in=concrete_integer_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(start=0, stop=9, output_field=models.BigIntegerField)
            .filter(term__in=Subquery(concrete_integer_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDecimalModel:
    """Make sure we can create and use Decimal sequences"""

    def test_decimalfield_variations(self):
        """Run through some variations."""
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=models.DecimalField,
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                output_field=models.DecimalField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=decimal.Decimal("1.00"),
                stop=decimal.Decimal("1.00"),
                step=decimal.Decimal("1.00"),
                output_field=models.DecimalField,
            ).count()
            == 1
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                include_id=True,
                output_field=models.DecimalField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                include_id=True,
                output_field=models.DecimalField,
            )
            .last()
            .id
            == 5
        )

    def test_decimalfield_concrete_instances(self):
        """Test working with concrete instances."""
        decimal_test = generate_series(
            start=decimal.Decimal("0.00"),
            stop=decimal.Decimal("9.00"),
            step=decimal.Decimal("1.00"),
            output_field=models.DecimalField,
        )
        assert decimal_test.count() == 10
        assert decimal_test.first().term == decimal.Decimal("0.00")
        assert decimal_test.last().term == decimal.Decimal("9.00")
        decimal_test_sum = decimal_test.aggregate(int_sum=Sum("term"))
        assert decimal_test_sum["int_sum"] == decimal.Decimal("45.00")

        # Create concrete instances
        for idx in range(0, 10):
            ConcreteDecimalTest.objects.create(some_field=idx)

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
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=models.DecimalField,
            )
            .filter(term__in=concrete_decimal_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=models.DecimalField,
            )
            .filter(term__in=Subquery(concrete_decimal_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDateModel:
    """Make sure we can create and use Date sequences"""

    def test_datefield_variations(self):
        """Run through some variations."""
        date_sequence = tuple(get_date_sequence())
        assert (
            generate_series(
                start=date_sequence[0], stop=date_sequence[-1], step="1 days", output_field=models.DateField
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=date_sequence[0], stop=date_sequence[-1], step="2 days", output_field=models.DateField
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=date_sequence[0], stop=date_sequence[0], step="1 days", output_field=models.DateField
            ).count()
            == 1
        )
        assert (
            generate_series(
                start=date_sequence[0],
                stop=date_sequence[-1],
                step="2 days",
                include_id=True,
                output_field=models.DateField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=date_sequence[0],
                stop=date_sequence[-1],
                step="2 days",
                include_id=True,
                output_field=models.DateField,
            )
            .last()
            .id
            == 5
        )

    def test_datefield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        date_sequence = tuple(get_date_sequence())
        date_test = generate_series(
            start=date_sequence[0], stop=date_sequence[-1], step="1 days", output_field=models.DateField
        )
        assert date_test.count() == 10
        assert date_test.first().term == date_sequence[0]
        assert date_test.last().term == date_sequence[-1]
        date_test_sum = date_test.aggregate(int_sum=Count("term"))
        assert date_test_sum["int_sum"] == 10

        # Create concrete instances
        for idx in date_sequence:
            ConcreteDateTest.objects.create(some_field=idx)

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
            generate_series(
                start=date_sequence[0], stop=date_sequence[-1], step="1 days", output_field=models.DateField
            )
            .filter(term__in=concrete_date_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(
                start=date_sequence[0], stop=date_sequence[-1], step="1 days", output_field=models.DateField
            )
            .filter(term__in=Subquery(concrete_date_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDateTimeModel:
    """Make sure we can create and use DateTime sequences"""

    def test_datetimefield_variations(self):
        """Create concrete instances."""
        datetime_sequence = tuple(get_datetime_sequence())

        # Run through some variations
        assert (
            generate_series(
                start=datetime_sequence[0], stop=datetime_sequence[-1], step="1 days", output_field=models.DateTimeField
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=datetime_sequence[0], stop=datetime_sequence[-1], step="2 days", output_field=models.DateTimeField
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=datetime_sequence[0], stop=datetime_sequence[0], step="1 days", output_field=models.DateTimeField
            ).count()
            == 1
        )
        assert (
            generate_series(
                start=datetime_sequence[0],
                stop=datetime_sequence[-1],
                step="2 days",
                include_id=True,
                output_field=models.DateTimeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=datetime_sequence[0],
                stop=datetime_sequence[-1],
                step="2 days",
                include_id=True,
                output_field=models.DateTimeField,
            )
            .last()
            .id
            == 5
        )

    def test_datetimefield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        datetime_sequence = tuple(get_datetime_sequence())
        datetime_test = generate_series(
            start=datetime_sequence[0], stop=datetime_sequence[-1], step="1 days", output_field=models.DateTimeField
        )

        assert datetime_test.count() == 10
        assert datetime_test.first().term == datetime_sequence[0]
        assert datetime_test.last().term == datetime_sequence[-1]
        datetime_test_sum = datetime_test.aggregate(int_sum=Count("term"))
        assert datetime_test_sum["int_sum"] == 10

        for idx in datetime_sequence:
            ConcreteDateTimeTest.objects.create(some_field=idx)

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
            generate_series(
                start=datetime_sequence[0], stop=datetime_sequence[-1], step="1 days", output_field=models.DateTimeField
            )
            .filter(term__in=concrete_datetime_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(
                start=datetime_sequence[0], stop=datetime_sequence[-1], step="1 days", output_field=models.DateTimeField
            )
            .filter(term__in=Subquery(concrete_datetime_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestIntegerRangeModel:
    """Make sure we can create and use Integer Range sequences"""

    def test_integerfield_variations(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        integer_range_test = generate_series(start=0, stop=9, output_field=IntegerRangeField)

        integer_range_test.first().term
        assert integer_range_test.count() == 10


        integer_range_test_sum = integer_range_test.aggregate(int_sum=Count("term"))
        assert integer_range_test_sum["int_sum"] == 10

        assert integer_range_test.filter(term__contains=NumericRange(1, 2)).count() == 1

    def test_integerfield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        integer_range_test = generate_series(start=0, stop=9, output_field=IntegerRangeField)
        integer_range_sequence = tuple(NumericRange(idx, idx + 1, "[)") for idx in range(0, 10))

        assert integer_range_test.first().term == integer_range_sequence[0]
        assert integer_range_test.get(term__overlap=(0, 1)) == integer_range_test.first()
        assert integer_range_test.first().term == NumericRange(0, 1, "[)")
        assert integer_range_test.last().term == integer_range_sequence[-1]

        for item in integer_range_sequence:
            ConcreteIntegerRangeTest.objects.create(some_field=item)

        # Run through some variations
        assert generate_series(start=0, stop=9, output_field=IntegerRangeField).count() == 10
        assert generate_series(start=0, stop=9, step=2, output_field=IntegerRangeField).count() == 5
        assert generate_series(start=1, stop=1, output_field=IntegerRangeField).count() == 1
        assert generate_series(start=0, stop=9, step=2, include_id=True, output_field=IntegerRangeField).count() == 5
        assert generate_series(start=0, stop=9, step=2, include_id=True, output_field=IntegerRangeField).last().id == 5

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
            generate_series(start=0, stop=9, output_field=IntegerRangeField)
            .filter(term__in=concrete_integer_range_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(start=0, stop=9, output_field=IntegerRangeField)
            .filter(term__in=Subquery(concrete_integer_range_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDecimalRangeModel:
    """Test suite for Decimal Range sequences"""

    def test_create_and_use_decimal_range(self):
        """Test creating and using Decimal Range sequences"""
        decimal_range_sequence = tuple(
            NumericRange(decimal.Decimal(idx), decimal.Decimal(idx + 1), "[)") for idx in range(0, 10)
        )

        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=DecimalRangeField,
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                output_field=DecimalRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=decimal.Decimal("1.00"),
                stop=decimal.Decimal("1.00"),
                step=decimal.Decimal("1.00"),
                output_field=DecimalRangeField,
            ).count()
            == 1
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                include_id=True,
                output_field=DecimalRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("2.00"),
                include_id=True,
                output_field=DecimalRangeField,
            )
            .last()
            .id
            == 5
        )

    def test_decimal_range_queryset_operations(self):
        """Test queryset operations on Decimal Range sequences"""
        decimal_range_sequence = tuple(
            NumericRange(decimal.Decimal(idx), decimal.Decimal(idx + 1), "[)") for idx in range(0, 10)
        )

        decimal_range_test = generate_series(
            start=decimal.Decimal("0.00"),
            stop=decimal.Decimal("9.00"),
            step=decimal.Decimal("1.00"),
            output_field=DecimalRangeField,
        )
        assert decimal_range_test.count() == 10
        assert decimal_range_test.first().term == decimal_range_sequence[0]
        assert decimal_range_test.last().term == decimal_range_sequence[-1]

        decimal_range_test_sum = decimal_range_test.aggregate(int_sum=Count("term"))
        assert decimal_range_test_sum["int_sum"] == 10

    def test_querying_from_concrete_decimal_model(self):
        """Test querying from the concrete Decimal Range model"""
        decimal_range_test = generate_series(
            start=decimal.Decimal("0.00"),
            stop=decimal.Decimal("9.00"),
            step=decimal.Decimal("1.00"),
            output_field=DecimalRangeField,
        )
        decimal_range_sequence = tuple(
            NumericRange(decimal.Decimal(idx), decimal.Decimal(idx + 1), "[)") for idx in range(0, 10)
        )

        for item in decimal_range_sequence:
            ConcreteDecimalRangeTest.objects.create(some_field=item)

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
        assert subquery_exists_test.first().some_field.lower == decimal.Decimal("0.0")
        assert subquery_exists_test.first().some_field.upper == decimal.Decimal("1.0")
        assert subquery_exists_test.last().some_field.lower == decimal.Decimal("9.0")
        assert subquery_exists_test.last().some_field.upper == decimal.Decimal("10.0")

        subquery_exists_test2 = ConcreteDecimalRangeTest.objects.all().annotate(
            decimal_range_test=Exists(decimal_range_test_values)
        )
        assert subquery_exists_test2.first().some_field == decimal_range_sequence[0]
        assert subquery_exists_test2.last().some_field == decimal_range_sequence[-1]

        concrete_decimal_range_test_values = ConcreteDecimalRangeTest.objects.values("some_field")
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=DecimalRangeField,
            )
            .filter(term__in=concrete_decimal_range_test_values)
            .count()
            == 10
        )
        assert (
            generate_series(
                start=decimal.Decimal("0.00"),
                stop=decimal.Decimal("9.00"),
                step=decimal.Decimal("1.00"),
                output_field=DecimalRangeField,
            )
            .filter(term__in=Subquery(concrete_decimal_range_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDateRangeModel:
    """Test suite for Date Range sequences"""

    def test_create_and_use_date_range(self):
        """Test creating and using Date Range sequences"""
        date_range_sequence = [
            DateRange(
                timezone.now().date() + timezone.timedelta(days=idx),
                (timezone.now().date() + timezone.timedelta(days=idx + 1)),
                "[)",
            )
            for idx in range(0, 9)
        ]

        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=10),
                step="1 days",
                output_field=DateRangeField,
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=10),
                step="2 days",
                output_field=DateRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date(),
                step="1 days",
                output_field=DateRangeField,
            ).count()
            == 0
        )
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=10),
                step="2 days",
                include_id=True,
                output_field=DateRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=10),
                step="2 days",
                include_id=True,
                output_field=DateRangeField,
            )
            .last()
            .id
            == 5
        )

    def test_date_range_queryset_operations(self):
        """Test queryset operations on Date Range sequences"""
        date_range_sequence = [
            DateRange(
                timezone.now().date() + timezone.timedelta(days=idx),
                (timezone.now().date() + timezone.timedelta(days=idx + 1)),
                "[)",
            )
            for idx in range(0, 9)
        ]

        date_range_test = generate_series(
            start=timezone.now().date(),
            stop=timezone.now().date() + timezone.timedelta(days=9),
            step="1 days",
            output_field=DateRangeField,
        )
        assert date_range_test.count() == 9
        assert date_range_test.first().term == date_range_sequence[0]
        assert date_range_test.last().term == date_range_sequence[-1]

        date_range_test_sum = date_range_test.aggregate(int_sum=Count("term"))
        assert date_range_test_sum["int_sum"] == 9

    def test_querying_from_concrete_date_model(self):
        """Test querying from the concrete Date Range model"""
        date_range_test = generate_series(
            start=timezone.now().date(),
            stop=timezone.now().date() + timezone.timedelta(days=9),
            step="1 days",
            output_field=DateRangeField,
        )

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

        assert ConcreteDateRangeTest.objects.filter(some_field__in=date_range_test.values("term")).count() == 9
        assert (
            ConcreteDateRangeTest.objects.filter(some_field__in=Subquery(date_range_test.values("term"))).count() == 9
        )

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

        concrete_date_range_test_values = ConcreteDateRangeTest.objects.values("some_field")
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=9),
                step="1 days",
                output_field=DateRangeField,
            )
            .filter(term__in=concrete_date_range_test_values)
            .count()
            == 9
        )
        assert (
            generate_series(
                start=timezone.now().date(),
                stop=timezone.now().date() + timezone.timedelta(days=9),
                step="1 days",
                output_field=DateRangeField,
            )
            .filter(term__in=Subquery(concrete_date_range_test_values))
            .count()
            == 9
        )


@pytest.mark.django_db
class TestDateTimeRangeModel:
    """Test suite for DateTime Range sequences"""

    def test_create_and_use_datetime_range(self):
        """Test creating and using DateTime Range sequences"""
        datetime_range_sequence = [
            DateTimeTZRange(
                (timezone.now() + timezone.timedelta(days=idx)).replace(hour=1, minute=2, second=3, microsecond=4),
                (timezone.now() + timezone.timedelta(days=idx + 1)).replace(hour=1, minute=2, second=3, microsecond=4),
                "[)",
            )
            for idx in range(0, 9)
        ]

        assert (
            generate_series(
                start=timezone.now(),
                stop=timezone.now() + timezone.timedelta(days=10),
                step="1 days",
                output_field=DateTimeRangeField,
            ).count()
            == 10
        )
        assert (
            generate_series(
                start=timezone.now(),
                stop=timezone.now() + timezone.timedelta(days=10),
                step="2 days",
                output_field=DateTimeRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=timezone.now(),
                stop=timezone.now(),
                step="1 days",
                output_field=DateTimeRangeField,
            ).count()
            == 0
        )
        assert (
            generate_series(
                start=timezone.now(),
                stop=timezone.now() + timezone.timedelta(days=10),
                step="2 days",
                include_id=True,
                output_field=DateTimeRangeField,
            ).count()
            == 5
        )
        assert (
            generate_series(
                start=timezone.now(),
                stop=timezone.now() + timezone.timedelta(days=10),
                step="2 days",
                include_id=True,
                output_field=DateTimeRangeField,
            )
            .last()
            .id
            == 5
        )

    def test_datetime_range_queryset_operations(self):
        """Test queryset operations on DateTime Range sequences"""
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

        datetime_range_test = generate_series(
            start=first_dt_in_range, stop=last_dt_in_range, step="1 days", output_field=DateTimeRangeField
        )
        assert datetime_range_test.count() == 9
        assert datetime_range_test.first().term == datetime_range_sequence[0]
        assert datetime_range_test.last().term == datetime_range_sequence[-1]

        date_range_test_sum = datetime_range_test.aggregate(int_sum=Count("term"))
        assert date_range_test_sum["int_sum"] == 9

    def test_querying_from_concrete_datetime_model(self):
        """Test querying from the concrete DateTime Range model"""
        datetime_range_sequence = [
            DateTimeTZRange(
                (timezone.now() + timezone.timedelta(days=idx)).replace(hour=1, minute=2, second=3, microsecond=4),
                (timezone.now() + timezone.timedelta(days=idx + 1)).replace(hour=1, minute=2, second=3, microsecond=4),
                "[)",
            )
            for idx in range(0, 9)
        ]

        for idx in datetime_range_sequence:
            ConcreteDateTimeRangeTest.objects.create(some_field=idx)

        first_dt_in_range = datetime_range_sequence[0].lower
        last_dt_in_range = datetime_range_sequence[-1].upper

        datetime_range_test = generate_series(
            start=first_dt_in_range, stop=last_dt_in_range, step="1 days", output_field=DateTimeRangeField
        )

        assert ConcreteDateTimeRangeTest.objects.filter(some_field__in=datetime_range_test.values("term")).count() == 9
        assert (
            ConcreteDateTimeRangeTest.objects.filter(
                some_field__in=Subquery(datetime_range_test.values("term"))
            ).count()
            == 9
        )

        datetime_range_test_values = datetime_range_test.filter(term=OuterRef("some_field")).values("term")
        assert (
            ConcreteDateTimeRangeTest.objects.filter(some_field__in=Subquery(datetime_range_test_values)).count() == 9
        )

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

        concrete_datetime_range_test_values = ConcreteDateTimeRangeTest.objects.values("some_field")
        assert (
            generate_series(
                start=datetime_range_sequence[0].lower,
                stop=datetime_range_sequence[-1].upper,
                step="1 days",
                output_field=DateTimeRangeField,
            )
            .filter(term__in=concrete_datetime_range_test_values)
            .count()
            == 9
        )
        assert (
            generate_series(
                start=datetime_range_sequence[0].lower,
                stop=datetime_range_sequence[-1].upper,
                step="1 days",
                output_field=DateTimeRangeField,
            )
            .filter(term__in=Subquery(concrete_datetime_range_test_values))
            .count()
            == 9
        )


@pytest.mark.django_db
class TestTypeChecking:
    """Test the type checking functions."""

    def test_get_output_field_class_standard_fields(self):
        """Test that the correct output field is returned for standard fields."""
        assert get_output_field_class(10) == models.IntegerField
        assert get_output_field_class(decimal.Decimal("10.0")) == models.DecimalField
        assert get_output_field_class(timezone.datetime.today().date()) == models.DateField
        assert get_output_field_class(timezone.now()) == models.DateTimeField

        with pytest.raises(ModelFieldNotSupported):
            get_output_field_class(start=True, span=10)

    def test_get_output_field_class_range_fields(self):
        """Test that the correct output field is returned for range fields."""
        assert get_output_field_class(10, span=1) == IntegerRangeField
        assert get_output_field_class(decimal.Decimal("10.0"), span=decimal.Decimal("1.0")) == DecimalRangeField
        assert (
            get_output_field_class(timezone.datetime.today().date(), span=timezone.datetime.today().date())
            == DateRangeField
        )
        assert get_output_field_class(timezone.now(), span=timezone.now()) == DateTimeRangeField

    def test_get_output_field_class_invalid_field(self):
        """Test that an exception is raised when an invalid field is passed."""
        with pytest.raises(ModelFieldNotSupported):
            get_output_field_class("string")

    def test_get_value_field_class_with_iterable(self):
        """Test that the correct value field is returned for an iterable."""
        assert get_value_field_class(None, (1, 2, 3)) == models.IntegerField
        assert get_value_field_class(None, (decimal.Decimal("10.0"), decimal.Decimal("20.0"))) == models.DecimalField
        assert get_value_field_class(None, ("a", "b", "c")) == models.CharField

    def test_get_value_field_class_invalid_value(self):
        """Test that an exception is raised when an invalid value is passed."""
        with pytest.raises(ModelFieldNotSupported):
            get_value_field_class(None, ([], [], []))

    def test_get_type_checking_dict(self):
        """Test that the correct type checking dict is returned."""
        assert get_type_checking_dict(models.IntegerField) == {
            "start_type": [int],
            "stop_type": [int],
            "step_type": [int],
            "span_type": None,
            "field_type": models.IntegerField,
            "range": False,
        }

        assert get_type_checking_dict(models.DecimalField) == {
            "start_type": [int, decimal.Decimal],
            "stop_type": [int, decimal.Decimal],
            "step_type": [int, decimal.Decimal],
            "span_type": None,
            "field_type": models.DecimalField,
            "range": False,
        }

        assert get_type_checking_dict(IntegerRangeField) == {
            "start_type": [int],
            "stop_type": [int],
            "step_type": [int],
            "span_type": [int],
            "field_type": IntegerRangeField,
            "range": True,
        }

        assert get_type_checking_dict(DecimalRangeField) == {
            "start_type": [int, decimal.Decimal],
            "stop_type": [int, decimal.Decimal],
            "step_type": [int, decimal.Decimal],
            "span_type": [int, decimal.Decimal],
            "field_type": DecimalRangeField,
            "range": True,
        }

    def test_get_type_checking_dict_invalid_field(self):
        """Test that an exception is raised when an invalid field is passed."""
        with pytest.raises(ModelFieldNotSupported):
            get_type_checking_dict(models.CharField)


@pytest.mark.django_db
class TestGenerateSeries:
    """Test the generate_series function."""

    def test_generate_series_queryset_and_iterable_error(self):
        """Test that providing both a queryset and an iterable raises ValueError."""
        for idx in range(0, 10):
            ConcreteIntegerTest.objects.create(some_field=idx)
        with pytest.raises(ValueError, match="Cannot provide both a queryset and an iterable for Cartesian product"):
            generate_series(
                start=1,
                stop=10,
                queryset=ConcreteIntegerTest.objects.all(),
                iterable=[1, 2, 3],
            )

    def test_generate_series_invalid_default_bounds(self):
        """Test that providing invalid default bounds raises ValueError."""
        with pytest.raises(ValueError, match="Value of default_bounds must be one of:"):
            generate_series(
                start=decimal.Decimal("1.0"),
                stop=decimal.Decimal("10.0"),
                output_field=models.DecimalField,
                default_bounds="invalid_bounds",
            )

    def test_generate_series_with_decimal_field(self):
        """Test generating series with a DecimalField."""
        queryset = generate_series(
            start=decimal.Decimal("1.0"),
            stop=decimal.Decimal("10.0"),
            step=decimal.Decimal("1.0"),
            output_field=models.DecimalField,
            max_digits=5,
            decimal_places=2,
        )
        assert queryset.model._meta.get_field("term").max_digits == 5
        assert queryset.model._meta.get_field("term").decimal_places == 2

    def test_generate_series_with_date_range(self):
        """Test generating series with a DateField."""
        queryset = generate_series(
            start=timezone.datetime(2023, 1, 1).date(),
            stop=timezone.datetime(2023, 1, 10).date(),
            step="1 day",
            output_field=models.DateField,
        )
        assert queryset.count() == 10


@pytest.mark.django_db
class TestMakeModelClass:
    """Test the _make_model_class function."""

    def test_make_model_class_invalid_field(self):
        """Test that an exception is raised when an invalid field is passed."""
        with pytest.raises(ModelFieldNotSupported, match="Invalid model field type used to generate series"):
            _make_model_class(
                output_field=models.CharField,  # Invalid field type
                include_id=True,
                max_digits=None,
                decimal_places=None,
                default_bounds=None,
            )

    def test_make_model_class_valid_range_bounds(self):
        """Test that the correct model class is returned with valid range bounds."""
        model_class = _make_model_class(
            output_field=DecimalRangeField,
            include_id=False,
            max_digits=10,
            decimal_places=2,
            default_bounds="[)",
        )
        assert model_class._meta.get_field("term").default_bounds == "[)"


@pytest.mark.django_db
class TestHelperFunctions:
    """Test the helper functions."""

    def test_get_term_dict_with_default_bounds(self):
        """Test that the correct term dict is returned with default bounds."""
        term_dict = get_term_dict(
            output_field=DecimalRangeField,
            include_id=False,
            max_digits=10,
            decimal_places=2,
            default_bounds="[)",
        )
        assert term_dict["default_bounds"] == "[)"

    def test_get_value_dict_for_decimal_field(self):
        """Test that the correct value dict is returned for a DecimalField."""
        value_dict = get_value_dict(models.DecimalField, max_digits=10, decimal_places=2)
        assert value_dict["max_digits"] == 10
        assert value_dict["decimal_places"] == 2

    def test_get_auto_field_import_error(self, monkeypatch):
        """Test that an ImportError is raised when the auto field cannot be imported."""
        monkeypatch.setattr("django_generate_series.models.DGS_DEFAULT_AUTO_FIELD", "invalid.module.path")
        with pytest.raises(ImproperlyConfigured, match="The settings refer to the module 'invalid.module.path'"):
            _get_auto_field()
