# Usage Examples

## Basic integer sequence example

Generate a sequence of every third integer from -12 to 12.

```python
integer_sequence = IntegerTest.objects.generate_series([-12, 13, 3])

for item in integer_sequence:
    print(item.id)

""" Example:
    -12
    -9
    -6
    -3
    0
    3
    6
    9
    12
"""
```

Resulting SQL

```sql
SELECT
  "core_integertest"."id"
FROM
  (
    SELECT
      generate_series(-12, 13, 3) id
  ) AS core_integertest;
```

## Example with decimals

Generate a sequence of decimal values, starting from 0.000 and increasing by 1.234, until reaching 10.000

```python
import decimal

decimal_sequence = DecimalTest.objects.generate_series(
    [decimal.Decimal("0.000"), decimal.Decimal("10.000"), decimal.Decimal("1.234")]
)
decimal_sequence.first().id

for item in decimal_sequence:
    print(item.id)

""" Example:
    0.000
    1.234
    2.468
    3.702
    4.936
    6.170
    7.404
    8.638
    9.872
"""
```

Resulting SQL

```sql
SELECT
  "core_decimaltest"."id"
FROM
  (
    SELECT
      generate_series(0.000, 10.000, 1.234) id
  ) AS core_decimaltest;
```

## Get summed costs for orders placed every other day over the past month

Given a model like this (included in tests.example.core.models):

```python
class SimpleOrder(models.Model):
    order_date = models.DateField()
    cost = models.IntegerField()
```

In this example, we want to get the summed costs for orders placed on every other day over the past month. Yes, this is a bit nonsensical, but it provides a pretty good example of how to use django-generate-series.

```python
import random
from django.db.models import OuterRef, Subquery, Sum
from tests.example.core.random_utils import get_random_date
from tests.example.core.models import SimpleOrder

# Get the current datetime and the datetime 30 days ago
now = timezone.now()
previous = now - timezone.timedelta(days=30)

def random_date_in_past_month():
    # Generate a radom date within the past 30 days
    return get_random_date(min_date=previous, max_timedelta=timezone.timedelta(days=30))

for x in range(0, 30):
    # Create 30 SimpleOrder instances with random date and a cost between $1 and $50
    SimpleOrder.objects.create(
        order_date=random_date_in_past_month(), cost=random.randrange(1, 50)
    )

# Create a Subquery of annotated SimpleOrder objects
simple_order_subquery = (
    SimpleOrder.objects.filter(order_date=OuterRef("id"))
    .order_by()
    .values("order_date")
    .annotate(sum_of_cost=Sum("cost"))
    .values("sum_of_cost")
)

# Our DateTest is expecting date values, so update our variables
previous = previous.date()
now = now.date()

# Annotate the generated DateTest sequence instances with the annotated Subquery
date_sequence_queryset = DateTest.objects.generate_series(
    [previous, now, "2 days"]
).annotate(daily_order_costs=Subquery(simple_order_subquery))

# Print out all of the SimpleOrder objects (these are randomly generated, so your results may vary)
for item in SimpleOrder.objects.order_by("order_date"):
    print(item.order_date, item.cost)


""" Example:
    2022-03-30 12
    2022-03-31 49
    2022-03-31 28
    2022-04-01 41
    2022-04-02 22
    2022-04-03 30
    2022-04-03 29
    2022-04-03 44
    2022-04-03 15
    2022-04-05 18
    2022-04-05 47
    2022-04-05 2
    2022-04-05 30
    2022-04-06 19
    2022-04-08 39
    2022-04-11 4
    2022-04-11 31
    2022-04-11 6
    2022-04-11 31
    2022-04-14 6
    2022-04-15 35
    2022-04-16 41
    2022-04-18 15
    2022-04-19 18
    2022-04-19 19
    2022-04-19 31
    2022-04-19 36
    2022-04-21 36
    2022-04-22 1
    2022-04-22 45
"""

# Print out the date_sequence_queryset
#    Remember this is the sum of order costs for every other day over the past month
for item in date_sequence_queryset:
    print(item.id, item.daily_order_costs)

""" Example:
    2022-03-24 00:00:00+00:00 None
    2022-03-26 00:00:00+00:00 None
    2022-03-28 00:00:00+00:00 None
    2022-03-30 00:00:00+00:00 12
    2022-04-01 00:00:00+00:00 41
    2022-04-03 00:00:00+00:00 118
    2022-04-05 00:00:00+00:00 97
    2022-04-07 00:00:00+00:00 None
    2022-04-09 00:00:00+00:00 None
    2022-04-11 00:00:00+00:00 72
    2022-04-13 00:00:00+00:00 None
    2022-04-15 00:00:00+00:00 35
    2022-04-17 00:00:00+00:00 None
    2022-04-19 00:00:00+00:00 104
    2022-04-21 00:00:00+00:00 36
    2022-04-23 00:00:00+00:00 None
"""
```

The resulting SQL would look something like

```sql
SELECT
  "core_datetest"."id",
  (
    SELECT
      SUM(U0."cost") AS "sum_of_cost"
    FROM
      "core_simpleorder" U0
    WHERE
      U0."order_date" = "core_datetest"."id"
    GROUP BY
      U0."order_date"
  ) AS "daily_order_costs"
FROM
  (
    SELECT
      generate_series('2022-03-24' :: date, '2022-04-23' :: date, '2 days') id
  ) AS core_datetest;
```

## Work with a series of datetime ranges

This example creates a sequence of date ranges, each seven day in length from today to 90 days from now. Then, similar to the previous example, we will sum all of the tickets with an event_datetime which overlaps with a range.

Given a model like this (included in tests.example.core.models).

```python
class Event(models.Model):
    event_datetime = models.DateTimeField()
    ticket_qty = models.IntegerField()
    false_field = models.BooleanField(default=False)
```
*Note: As a workaround for an oddity in django's ORM, we have included a `false_field`, which always evaluates to `False`. This allows us to perform a GROUP_BY in the SQL, since the datetime of each Event may be different, but we want to to group them if they fall in the same 7-day period. We would welcome improved approaches.*

### Create some random events

```python
import random
from django.db.models import OuterRef, Subquery, Sum, Count
from tests.example.core.random_utils import get_random_datetime
from tests.example.core.models import Event

# Get the current datetime and the datetime 90 days ago
now = timezone.now()
later = (now + timezone.timedelta(days=90))

def random_datetime_in_past_month():
    # Generate a radom date within the past 90 days
    return get_random_datetime(min_date=now, max_timedelta=timezone.timedelta(days=90))

for x in range(0, 30):
    # Create 30 Event instances with random datetime and a ticket_qty between 1 and 5
    event = Event.objects.create(
        event_datetime=random_datetime_in_past_month(),
        ticket_qty=random.randrange(1, 5),
    )

# Create a Subquery of annotated Event objects
for item in Event.objects.all().order_by("event_datetime"):
    print(item.event_datetime, item.ticket_qty)

""" Example (broken up by 7-day segments for clarity):
    2022-04-26 04:45:31.036525+00:00 2
    2022-04-27 09:54:52.036525+00:00 2

    2022-05-01 23:50:20.036525+00:00 4
    2022-05-07 09:09:30.036525+00:00 3

    2022-05-09 07:00:31.036525+00:00 1
    2022-05-10 09:20:25.036525+00:00 1
    2022-05-13 16:51:43.036525+00:00 4

    2022-05-15 05:59:32.036525+00:00 2
    2022-05-19 21:01:29.036525+00:00 4

    2022-05-22 15:16:09.036525+00:00 1
    2022-05-23 14:39:58.036525+00:00 3
    2022-05-27 14:47:12.036525+00:00 1

    2022-05-30 05:08:26.036525+00:00 4

    2022-06-11 20:21:58.036525+00:00 3

    2022-06-13 08:56:58.036525+00:00 1
    2022-06-14 16:43:50.036525+00:00 1
    2022-06-16 14:21:21.036525+00:00 2
    2022-06-17 17:11:16.036525+00:00 1
    2022-06-18 14:56:16.036525+00:00 2

    2022-06-19 07:59:22.036525+00:00 3
    2022-06-20 14:42:50.036525+00:00 1

    2022-07-02 10:20:46.036525+00:00 4

    2022-07-04 01:33:01.036525+00:00 4
    2022-07-05 06:14:31.036525+00:00 2
    2022-07-05 20:57:33.036525+00:00 3
    2022-07-07 05:08:14.036525+00:00 3

    2022-07-11 09:02:26.036525+00:00 1
    2022-07-12 02:12:02.036525+00:00 2
    2022-07-12 12:16:11.036525+00:00 3

    2022-07-22 17:08:46.036525+00:00 2
"""

event_subquery = (
    Event.objects.filter(event_datetime__contained_by=OuterRef("id"))
    .order_by()
    .values("false_field")
    .annotate(sum_of_tickets=Sum("ticket_qty"))
    .values("sum_of_tickets")
)
```

### Generate and annotate the datetime ranges

```python
datetime_range_sequence = (
    DateTimeRangeTest.objects.generate_series([now, later, "7 days"])
    .annotate(ticket_quantities=Subquery(event_subquery))
    .order_by("id")
)

for item in datetime_range_sequence:
    print(item.id, item.ticket_quantities)

""" Example:
    [2022-04-24 03:15:08.036525+00:00, 2022-05-01 03:15:08.036525+00:00) 4
    [2022-05-01 03:15:08.036525+00:00, 2022-05-08 03:15:08.036525+00:00) 7
    [2022-05-08 03:15:08.036525+00:00, 2022-05-15 03:15:08.036525+00:00) 6
    [2022-05-15 03:15:08.036525+00:00, 2022-05-22 03:15:08.036525+00:00) 6
    [2022-05-22 03:15:08.036525+00:00, 2022-05-29 03:15:08.036525+00:00) 5
    [2022-05-29 03:15:08.036525+00:00, 2022-06-05 03:15:08.036525+00:00) 4
    [2022-06-05 03:15:08.036525+00:00, 2022-06-12 03:15:08.036525+00:00) 3
    [2022-06-12 03:15:08.036525+00:00, 2022-06-19 03:15:08.036525+00:00) 7
    [2022-06-19 03:15:08.036525+00:00, 2022-06-26 03:15:08.036525+00:00) 4
    [2022-06-26 03:15:08.036525+00:00, 2022-07-03 03:15:08.036525+00:00) 4
    [2022-07-03 03:15:08.036525+00:00, 2022-07-10 03:15:08.036525+00:00) 12
    [2022-07-10 03:15:08.036525+00:00, 2022-07-17 03:15:08.036525+00:00) 6
"""
```

The resulting SQL would look something like

```sql
SELECT
  "core_datetimerangetest"."id",
  (
    SELECT
      SUM(U0."ticket_qty") AS "sum_of_tickets"
    FROM
      "core_event" U0
    WHERE
      U0."event_datetime" <@ "core_datetimerangetest"."id" :: tstzrange
    GROUP BY
      U0."false_field"
  ) AS "ticket_quantities"
FROM
  (
    SELECT
      tstzrange((lag(a) OVER()), a, '[)') AS id
    FROM
      generate_series(
        timestamptz '2022-04-24T03:15:08.036525+00:00' :: timestamptz,
        timestamptz '2022-07-23T03:15:08.036525+00:00' :: timestamptz,
        interval '7 days'
      ) AS a OFFSET 1
  ) AS core_datetimerangetest
ORDER BY
  "core_datetimerangetest"."id" ASC;

```

## Use the previous example