# Usage Examples

## Basic integer sequence example

Generate a sequence of every third integer from -12 to 12.

```python
from django.db import models
from django_generate_series.models import generate_series

integer_sequence = generate_series(-12, 13, 3, output_field=models.IntegerField)

for item in integer_sequence:
    print(item.term)

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
  "django_generate_series_integerfieldseries"."term"
FROM
  (
    SELECT
      generate_series(-12, 13, 3) term
  ) AS django_generate_series_integerfieldseries;
```


## Basic integer sequence example with id

Generate a sequence of every third integer from -12 to 12, along with an auto-incrementing id field.

To include the `id` field in any sequence, set `include_id=True`. This does add a small increase in overhead.

```python
from django.db import models
from django_generate_series.models import generate_series

integer_sequence = generate_series(-12, 13, 3, include_id=True, output_field=models.IntegerField)

for item in integer_sequence:
    print(item.id, item.term)

""" Example:
    1 -12
    2 -9
    3 -6
    4 -3
    5 0
    6 3
    7 6
    8 9
    9 12
"""
```

Resulting SQL

```sql
SELECT
  "django_generate_series_integerfieldseries"."id",
  "django_generate_series_integerfieldseries"."term"
FROM
  (
    SELECT
      row_number() over () as id,
      "term"
    FROM
      (
        SELECT
          generate_series(-12, 13, 3) term
      ) AS seriesquery
  ) AS django_generate_series_integerfieldseries;

```

## Example with decimals

Generate a sequence of decimal values, starting from 0.000 and increasing by 1.234, until reaching 10.000

```python
import decimal

decimal_sequence = generate_series(
    decimal.Decimal("0.000"), decimal.Decimal("10.000"), decimal.Decimal("1.234"), output_field=models.DecimalField,
)

for item in decimal_sequence:
    print(item.term)

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
  "django_generate_series_decimalfieldseries"."term"
FROM
  (
    SELECT
      generate_series(0.000, 10.000, 1.234) term
  ) AS django_generate_series_decimalfieldseries;
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
    SimpleOrder.objects.filter(order_date=OuterRef("term"))
    .order_by()
    .values("order_date")
    .annotate(sum_of_cost=Sum("cost"))
    .values("sum_of_cost")
)

# Our DateTest is expecting date values, so update our variables
previous = previous.date()
now = now.date()

# Annotate the generated DateTest sequence instances with the annotated Subquery
date_sequence_queryset = generate_series(
    previous, now, "2 days", output_field=models.DateField,
).annotate(daily_order_costs=Subquery(simple_order_subquery))

# Print out all of the SimpleOrder objects (these are randomly generated, so your results may vary)
for item in SimpleOrder.objects.order_by("order_date"):
    print(item.order_date, item.cost)


""" Example:
    2022-03-28 3
    2022-03-31 26
    2022-04-01 16
    2022-04-01 19
    2022-04-02 19
    2022-04-03 40
    2022-04-05 29
    2022-04-07 26
    2022-04-07 48
    2022-04-09 36
    2022-04-09 24
    2022-04-11 24
    2022-04-12 29
    2022-04-13 25
    2022-04-14 43
    2022-04-15 41
    2022-04-15 30
    2022-04-16 30
    2022-04-18 6
    2022-04-19 17
    2022-04-20 41
    2022-04-21 48
    2022-04-23 19
    2022-04-23 31
    2022-04-23 24
    2022-04-23 36
    2022-04-23 45
    2022-04-24 11
    2022-04-24 20
    2022-04-26 2
"""

# Print out the date_sequence_queryset
#    Remember this is the sum of order costs for every other day over the past month
for item in date_sequence_queryset:
    print(item.term, item.daily_order_costs)

""" Example:
    2022-03-28 00:00:00+00:00 3
    2022-03-30 00:00:00+00:00 None
    2022-04-01 00:00:00+00:00 35
    2022-04-03 00:00:00+00:00 40
    2022-04-05 00:00:00+00:00 29
    2022-04-07 00:00:00+00:00 74
    2022-04-09 00:00:00+00:00 60
    2022-04-11 00:00:00+00:00 24
    2022-04-13 00:00:00+00:00 25
    2022-04-15 00:00:00+00:00 71
    2022-04-17 00:00:00+00:00 None
    2022-04-19 00:00:00+00:00 17
    2022-04-21 00:00:00+00:00 48
    2022-04-23 00:00:00+00:00 155
    2022-04-25 00:00:00+00:00 None
    2022-04-27 00:00:00+00:00 None
"""
```

The resulting SQL would look something like

```sql
SELECT
  "django_generate_series_datefieldseries"."term",
  (
    SELECT
      SUM(U0."cost") AS "sum_of_cost"
    FROM
      "core_simpleorder" U0
    WHERE
      U0."order_date" = "django_generate_series_datefieldseries"."term"
    GROUP BY
      U0."order_date"
  ) AS "daily_order_costs"
FROM
  (
    SELECT
      generate_series('2022-03-28' :: date, '2022-04-27' :: date, '2 days') :: date term
  ) AS django_generate_series_datefieldseries;

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
from django.contrib.postgres.fields import DateTimeRangeField
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
    2022-04-28 14:27:42.986299+00:00 3
    2022-04-29 16:58:27.986299+00:00 3

    2022-05-05 11:34:05.986299+00:00 1
    2022-05-06 23:06:52.986299+00:00 2
    2022-05-10 12:08:59.986299+00:00 2

    2022-05-13 23:51:26.986299+00:00 2

    2022-05-18 06:53:05.986299+00:00 3
    2022-05-18 20:22:20.986299+00:00 3
    2022-05-24 21:28:06.986299+00:00 2

    2022-05-26 03:34:56.986299+00:00 1

    2022-06-01 06:15:13.986299+00:00 1
    2022-06-03 15:44:08.986299+00:00 4

    2022-06-08 13:28:02.986299+00:00 3
    2022-06-12 14:09:17.986299+00:00 3

    2022-06-17 14:44:59.986299+00:00 3
    2022-06-19 16:25:02.986299+00:00 1

    2022-06-25 22:49:32.986299+00:00 3
    2022-06-26 11:07:40.986299+00:00 1

    2022-06-30 10:22:05.986299+00:00 3
    2022-06-30 21:38:59.986299+00:00 2
    2022-07-03 15:04:01.986299+00:00 1

    2022-07-07 13:08:58.986299+00:00 1
    2022-07-07 18:41:42.986299+00:00 2
    2022-07-09 18:21:40.986299+00:00 2
    2022-07-11 20:32:52.986299+00:00 1

    2022-07-16 22:46:10.986299+00:00 3
    2022-07-17 05:00:04.986299+00:00 4

    2022-07-20 11:40:06.986299+00:00 1
    2022-07-23 12:53:13.986299+00:00 3
    2022-07-24 21:33:46.986299+00:00 2
"""

event_subquery = (
    Event.objects.filter(event_datetime__contained_by=OuterRef("term"))
    .order_by()
    .values("false_field")
    .annotate(sum_of_tickets=Sum("ticket_qty"))
    .values("sum_of_tickets")
)
```

### Generate and annotate the datetime ranges

```python
datetime_range_sequence = (
    generate_series(now, later, "7 days", output_field=DateTimeRangeField)
    .annotate(ticket_quantities=Subquery(event_subquery))
    .order_by("term")
)

for item in datetime_range_sequence:
    print(item.term, item.ticket_quantities)

""" Example:
    [2022-04-27 01:39:19.986299+00:00, 2022-05-04 01:39:19.986299+00:00) 6
    [2022-05-04 01:39:19.986299+00:00, 2022-05-11 01:39:19.986299+00:00) 5
    [2022-05-11 01:39:19.986299+00:00, 2022-05-18 01:39:19.986299+00:00) 2
    [2022-05-18 01:39:19.986299+00:00, 2022-05-25 01:39:19.986299+00:00) 8
    [2022-05-25 01:39:19.986299+00:00, 2022-06-01 01:39:19.986299+00:00) 1
    [2022-06-01 01:39:19.986299+00:00, 2022-06-08 01:39:19.986299+00:00) 5
    [2022-06-08 01:39:19.986299+00:00, 2022-06-15 01:39:19.986299+00:00) 6
    [2022-06-15 01:39:19.986299+00:00, 2022-06-22 01:39:19.986299+00:00) 4
    [2022-06-22 01:39:19.986299+00:00, 2022-06-29 01:39:19.986299+00:00) 4
    [2022-06-29 01:39:19.986299+00:00, 2022-07-06 01:39:19.986299+00:00) 6
    [2022-07-06 01:39:19.986299+00:00, 2022-07-13 01:39:19.986299+00:00) 6
    [2022-07-13 01:39:19.986299+00:00, 2022-07-20 01:39:19.986299+00:00) 7
"""
```

The resulting SQL would look something like

```sql
SELECT
  "django_generate_series_datetimerangefieldseries"."term",
  (
    SELECT
      SUM(U0."ticket_qty") AS "sum_of_tickets"
    FROM
      "core_event" U0
    WHERE
      U0."event_datetime" < @ "django_generate_series_datetimerangefieldseries"."term" :: tstzrange
    GROUP BY
      U0."false_field"
  ) AS "ticket_quantities"
FROM
  (
    SELECT
      tstzrange((lag(a) OVER()), a, '[)') AS term
    FROM
      generate_series(
            timestamptz '2022-04-27T01:39:19.986299+00:00' :: timestamptz,
            timestamptz '2022-07-26T01:39:19.986299+00:00' :: timestamptz,
        interval '7 days'
      ) AS a OFFSET 1
  ) AS django_generate_series_datetimerangefieldseries
ORDER BY
  "django_generate_series_datetimerangefieldseries"."term" ASC;
```
