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
    Count,
    Exists,
    OuterRef,
    Subquery,
    Sum,
)
from django.utils import timezone
from psycopg.types.range import DateRange, Int4Range, NumericRange, TimestamptzRange as DateTimeTZRange

from django_generate_series.exceptions import ModelFieldNotSupported
from django_generate_series.models import (
    _build_model_class_name,
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
from tests.example.core.sequence_utils import get_date_sequence, get_datetime_sequence


class TestSequenceUtils:
    """Make sure sequence_utils.py functions work correctly."""

    def test_get_datetime_sequence(self):
        """Make sure we can generate a sequence of datetimes."""
        now = timezone.now()

        assert get_datetime_sequence(start_datetime=now)
        dt_sequence = list(get_datetime_sequence(start_datetime=now))
        assert len(dt_sequence) == 10
        assert isinstance(dt_sequence[0], timezone.datetime)
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

        dt_sequence = list(get_datetime_sequence(start_datetime=now, end_datetime=now + timezone.timedelta(days=10)))
        assert len(dt_sequence) == 10
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

        with pytest.raises(ValueError, match="end_datetime is provided, it must be greater than start_datetime"):
            list(get_datetime_sequence(start_datetime=now, end_datetime=now - timezone.timedelta(days=9)))

        with pytest.raises(ValueError, match="num_steps value is provided, it must be positive"):
            list(get_datetime_sequence(num_steps=-10))

    def test_get_date_sequence(self):
        """Make sure we can generate a sequence of dates."""
        now = timezone.now()

        assert get_date_sequence(start_datetime=now)
        dt_sequence = list(get_date_sequence(start_datetime=now))
        assert len(dt_sequence) == 10
        assert isinstance(dt_sequence[0], datetime.date)
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)

        dt_sequence = list(get_date_sequence(start_datetime=now, end_datetime=now + timezone.timedelta(days=10)))
        assert len(dt_sequence) == 10
        assert dt_sequence[9] - dt_sequence[0] == timezone.timedelta(days=9)


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

        # Check that we can query from the generate series model
        concrete_integer_test_values = ConcreteIntegerTest.objects.values("some_field")
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

        # Check that we can query from the generate series model
        concrete_decimal_test_values = ConcreteDecimalTest.objects.values("some_field")
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

    def test_datefield_variations(self, date_sequence):
        """Run through some variations."""
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

    def test_datefield_concrete_instances(self, date_sequence):
        """Make sure we can create a QuerySet and perform basic operations."""
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

        # Check that we can query from the generate series model
        concrete_date_test_values = ConcreteDateTest.objects.values("some_field")
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

    def test_datetimefield_variations(self, datetime_sequence):
        """Run through some variations."""
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

    def test_datetimefield_concrete_instances(self, datetime_sequence):
        """Make sure we can create a QuerySet and perform basic operations."""
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

        # Check that we can query from the generate series model
        concrete_datetime_test_values = ConcreteDateTimeTest.objects.values("some_field")
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
        assert integer_range_test.count() == 10

        integer_range_test_sum = integer_range_test.aggregate(int_sum=Count("term"))
        assert integer_range_test_sum["int_sum"] == 10

        assert integer_range_test.filter(term__contains=Int4Range(1, 2)).count() == 1

    def test_integerfield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform basic operations."""
        integer_range_test = generate_series(start=0, stop=9, output_field=IntegerRangeField)
        integer_range_sequence = tuple(Int4Range(idx, idx + 1, "[)") for idx in range(0, 10))

        assert integer_range_test.first().term == integer_range_sequence[0]
        assert integer_range_test.get(term__overlap=(0, 1)) == integer_range_test.first()
        assert integer_range_test.first().term == Int4Range(0, 1, "[)")
        assert integer_range_test.last().term == integer_range_sequence[-1]

        for item in integer_range_sequence:
            ConcreteIntegerRangeTest.objects.create(some_field=item)

        # Check that we can query from the concrete model
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

        # Check that we can query from the generate series model
        concrete_integer_range_test_values = ConcreteIntegerRangeTest.objects.values("some_field")
        assert (
            generate_series(start=0, stop=9, output_field=IntegerRangeField)
            .filter(term__in=Subquery(concrete_integer_range_test_values))
            .count()
            == 10
        )


@pytest.mark.django_db
class TestDecimalRangeModel:
    """Test suite for Decimal Range sequences"""

    def test_decimalrangefield_variations(self):
        """Make sure we can create and use Decimal Range sequences."""
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

    def test_decimalrangefield_queryset_operations(self):
        """Make sure we can perform queryset operations on Decimal Range sequences."""
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

    def test_decimalrangefield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform subquery operations."""
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

        concrete_decimal_range_test_values = ConcreteDecimalRangeTest.objects.values("some_field")
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

    def test_daterangefield_variations(self):
        """Make sure we can create and use Date Range sequences."""
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

    def test_daterangefield_queryset_operations(self):
        """Make sure we can perform queryset operations on Date Range sequences."""
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

    def test_daterangefield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform subquery operations."""
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

        concrete_date_range_test_values = ConcreteDateRangeTest.objects.values("some_field")
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

    def test_datetimerangefield_variations(self):
        """Make sure we can create and use DateTime Range sequences."""
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

    def test_datetimerangefield_queryset_operations(self):
        """Make sure we can perform queryset operations on DateTime Range sequences."""
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

    def test_datetimerangefield_concrete_instances(self):
        """Make sure we can create a QuerySet and perform subquery operations."""
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

        concrete_datetime_range_test_values = ConcreteDateTimeRangeTest.objects.values("some_field")
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

    def test_get_value_field_class_with_queryset(self):
        """Test that the correct value field is returned for a queryset."""
        qs = ConcreteIntegerTest.objects.all()
        assert get_value_field_class(qs, None) == models.BigAutoField


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

    def test_start_greater_than_stop(self):
        """Test that start > stop raises ValueError."""
        with pytest.raises(ValueError, match="Start value must be smaller or equal to stop value"):
            generate_series(start=10, stop=0, output_field=models.IntegerField).count()

    def test_mismatched_start_stop_types(self):
        """Test that different start/stop types raises ValueError."""
        with pytest.raises(ValueError, match="Start and stop values must be of the same type"):
            generate_series(start=0, stop=decimal.Decimal("10.0"), output_field=models.DecimalField).count()

    def test_invalid_param_type(self):
        """Test that wrong param types raise ValueError."""
        with pytest.raises(ValueError, match="Start type of .* expected, but received type"):
            generate_series(start="bad", stop="worse", step="1", output_field=models.IntegerField).count()

    def test_step_none_accepted(self):
        """Test that step=None is accepted and defaults to 1 in the query."""
        qs = generate_series(start=0, stop=9, step=None, output_field=models.IntegerField)
        assert qs.count() == 10

    def test_range_field_with_explicit_span(self):
        """Test that providing span explicitly for a range field works."""
        qs = generate_series(start=0, stop=9, step=2, span=3, output_field=IntegerRangeField)
        assert qs.count() == 5
        # Each term should span 3 (e.g., [0, 3), [2, 5), ...)
        first = qs.first().term
        assert first.upper - first.lower == 3


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

    def test_get_value_dict_non_decimal_field(self):
        """Test that an empty dict is returned for non-decimal value fields."""
        assert get_value_dict(models.IntegerField, max_digits=10, decimal_places=2) == {}

    def test_build_model_class_name_with_queryset_marker(self):
        """Test that the model class name includes Qs when a queryset is provided."""
        name = _build_model_class_name(models.IntegerField, False, None, None, None, "placeholder", None)
        assert name == "IntegerFieldSeriesQs"

    def test_build_model_class_name_with_iterable_marker(self):
        """Test that the model class name includes It when an iterable is provided."""
        name = _build_model_class_name(models.IntegerField, False, None, None, None, None, (1, 2, 3))
        assert name == "IntegerFieldSeriesIt"

    def test_get_auto_field_import_error(self, monkeypatch):
        """Test that an ImportError is raised when the auto field cannot be imported."""
        monkeypatch.setattr("django_generate_series.models.DGS_DEFAULT_AUTO_FIELD", "invalid.module.path")
        with pytest.raises(ImproperlyConfigured, match="The settings refer to the module 'invalid.module.path'"):
            _get_auto_field()


@pytest.mark.django_db
class TestCartesianProduct:
    """Test Cartesian product with iterables."""

    def test_iterable_cartesian_product(self):
        """Test generating a Cartesian product with a list iterable."""
        qs = generate_series(start=0, stop=2, iterable=[10, 20, 30], output_field=models.IntegerField)
        assert qs.count() == 9  # 3 terms × 3 iterable items
        values = list(qs.values_list("term", "value"))
        terms = {v[0] for v in values}
        iter_values = {v[1] for v in values}
        assert terms == {0, 1, 2}
        assert iter_values == {10, 20, 30}
