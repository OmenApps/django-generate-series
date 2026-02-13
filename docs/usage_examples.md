# Usage Examples

## Basic integer sequence example

Generate a sequence of every third integer from -12 to 12.

```python
from django.db import models
from django_generate_series.models import generate_series

integer_sequence = generate_series(start=-12, stop=12, step=3, output_field=models.IntegerField)

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

Resulting SQL:

```sql
SELECT
  "django_generate_series_integerfieldseries"."term"
FROM
  (
    SELECT
      generate_series(-12, 12, 3) term
  ) AS django_generate_series_integerfieldseries;
```

## Basic integer sequence example with id

Generate a sequence of every third integer from -12 to 12, along with an auto-incrementing id field.

To include the `id` field in any sequence, set `include_id=True`. This does add a small increase in overhead.

```python
from django.db import models
from django_generate_series.models import generate_series

integer_sequence = generate_series(start=-12, stop=12, step=3, include_id=True, output_field=models.IntegerField)

for item in integer_sequence:
    print(item.id, item.term)

""" Example:
    1  -12
    2  -9
    3  -6
    4  -3
    5   0
    6   3
    7   6
    8   9
    9   12
"""
```

Resulting SQL:

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
          generate_series(-12, 12, 3) term
      ) AS seriesquery
  ) AS django_generate_series_integerfieldseries;

```

## Example with decimals

Generate a sequence of decimal values, starting from 0.000 and increasing by 1.234, until reaching 10.000

```python
import decimal
from django.db import models
from django_generate_series.models import generate_series

decimal_sequence = generate_series(
    start=decimal.Decimal("0.000"),
    stop=decimal.Decimal("10.000"),
    step=decimal.Decimal("1.234"),
    output_field=models.DecimalField,
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

Resulting SQL:

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

Given a model like this:

```python
from django.db import models

class SimpleOrder(models.Model):
    order_date = models.DateField()
    cost = models.IntegerField()
```

In this example, we want to get the summed costs for orders placed on every other day over the past month. Yes, this is a bit nonsensical, but it provides a pretty good example of how to use django-generate-series.

```python
import random
from datetime import timedelta
from django.db.models import OuterRef, Subquery, Sum
from django.utils import timezone

# Get the current datetime and the datetime 30 days ago
now = timezone.now()
previous = now - timedelta(days=30)

for x in range(0, 30):
    # Create 30 SimpleOrder instances with random date and a cost between $1 and $50
    random_date = (previous + timedelta(days=random.randint(0, 30))).date()
    SimpleOrder.objects.create(order_date=random_date, cost=random.randrange(1, 50))

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
    start=previous, stop=now, step="2 days", output_field=models.DateField,
).annotate(daily_order_costs=Subquery(simple_order_subquery))

# Print out all of the SimpleOrder objects (these are randomly generated, so your results may vary)
for item in SimpleOrder.objects.order_by("order_date"):
    print(item.order_date, item.cost)


""" Example:
    2026-03-28  3
    2026-03-31  26
    2026-04-01  16
    2026-04-01  19
    2026-04-02  19
    2026-04-03  40
    2026-04-05  29
    2026-04-07  26
    2026-04-07  48
    2026-04-09  36
    2026-04-09  24
    2026-04-11  24
    2026-04-12  29
    2026-04-13  25
    2026-04-14  43
    2026-04-15  41
    2026-04-15  30
    2026-04-16  30
    2026-04-18  6
    2026-04-19  17
    2026-04-20  41
    2026-04-21  48
    2026-04-23  19
    2026-04-23  31
    2026-04-23  24
    2026-04-23  36
    2026-04-23  45
    2026-04-24  11
    2026-04-24  20
    2026-04-26  2
"""

# Print out the date_sequence_queryset
#    Remember this is the sum of order costs for every other day over the past month
for item in date_sequence_queryset:
    print(item.term, item.daily_order_costs)

""" Example:
    2026-03-28 00:00:00+00:00  3
    2026-03-30 00:00:00+00:00  None
    2026-04-01 00:00:00+00:00  35
    2026-04-03 00:00:00+00:00  40
    2026-04-05 00:00:00+00:00  29
    2026-04-07 00:00:00+00:00  74
    2026-04-09 00:00:00+00:00  60
    2026-04-11 00:00:00+00:00  24
    2026-04-13 00:00:00+00:00  25
    2026-04-15 00:00:00+00:00  71
    2026-04-17 00:00:00+00:00  None
    2026-04-19 00:00:00+00:00  17
    2026-04-21 00:00:00+00:00  48
    2026-04-23 00:00:00+00:00  155
    2026-04-25 00:00:00+00:00  None
    2026-04-27 00:00:00+00:00  None
"""
```

The resulting SQL would look something like:

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
      generate_series('2026-03-28' :: date, '2026-04-27' :: date, '2 days') :: date term
  ) AS django_generate_series_datefieldseries;

```

## Work with a series of datetime ranges

This example creates a sequence of date ranges, each seven day in length from today to 90 days from now. Then, similar to the previous example, we will sum all of the tickets with an event_datetime which overlaps with a range.

Note the use of `Func` here bypasses Django's default 'group by' functionality, which allows us to select rows that fall within an entire range. Normally, django would try to group by specific matches, but we want to match anything that is contained within each range. (Thanks [@niccolomineo](https://twitter.com/niccolomineo) for the tip!)

Given a model like this:

```python
from django.db import models

class Event(models.Model):
    event_datetime = models.DateTimeField()
    ticket_qty = models.IntegerField()
```

### Create some random events

```python
import random
from datetime import timedelta
from django.contrib.postgres.fields import DateTimeRangeField
from django.db.models import OuterRef, Subquery, Sum
from django.utils import timezone
from django_generate_series.models import generate_series

# Get the current datetime and the datetime 90 days from now
now = timezone.now()
later = now + timedelta(days=90)
SECONDS_IN_90_DAYS = 90 * 24 * 3600

for x in range(0, 30):
    # Create 30 Event instances with random datetime and a ticket_qty between 1 and 5
    random_dt = now + timedelta(seconds=random.randint(0, SECONDS_IN_90_DAYS))
    Event.objects.create(event_datetime=random_dt, ticket_qty=random.randrange(1, 5))

# Create a Subquery of annotated Event objects
for item in Event.objects.all().order_by("event_datetime"):
    print(item.event_datetime, item.ticket_qty)

""" Example (broken up by 7-day segments for clarity):
    2026-04-28 14:27:42.986299+00:00  3
    2026-04-29 16:58:27.986299+00:00  3

    2026-05-05 11:34:05.986299+00:00  1
    2026-05-06 23:06:52.986299+00:00  2
    2026-05-10 12:08:59.986299+00:00  2

    2026-05-13 23:51:26.986299+00:00  2

    2026-05-18 06:53:05.986299+00:00  3
    2026-05-18 20:22:20.986299+00:00  3
    2026-05-24 21:28:06.986299+00:00  2

    2026-05-26 03:34:56.986299+00:00  1

    2026-06-01 06:15:13.986299+00:00  1
    2026-06-03 15:44:08.986299+00:00  4

    2026-06-08 13:28:02.986299+00:00  3
    2026-06-12 14:09:17.986299+00:00  3

    2026-06-17 14:44:59.986299+00:00  3
    2026-06-19 16:25:02.986299+00:00  1

    2026-06-25 22:49:32.986299+00:00  3
    2026-06-26 11:07:40.986299+00:00  1

    2026-06-30 10:22:05.986299+00:00  3
    2026-06-30 21:38:59.986299+00:00  2
    2026-07-03 15:04:01.986299+00:00  1

    2026-07-07 13:08:58.986299+00:00  1
    2026-07-07 18:41:42.986299+00:00  2
    2026-07-09 18:21:40.986299+00:00  2
    2026-07-11 20:32:52.986299+00:00  1

    2026-07-16 22:46:10.986299+00:00  3
    2026-07-17 05:00:04.986299+00:00  4

    2026-07-20 11:40:06.986299+00:00  1
    2026-07-23 12:53:13.986299+00:00  3
    2026-07-24 21:33:46.986299+00:00  2
"""

event_subquery = (
    Event.objects.filter(event_datetime__contained_by=OuterRef("term"))
    .order_by()
    .annotate(sum_of_tickets=Func(F("ticket_qty"), function="SUM"))
    .values("sum_of_tickets")
)
```

### Generate and annotate the datetime ranges (similar to above, but using '7 days' as step)

```python
datetime_range_sequence = (
    generate_series(start=now, stop=later, step="7 days", output_field=DateTimeRangeField)
    .annotate(ticket_quantities=Subquery(event_subquery))
    .order_by("term")
)

for item in datetime_range_sequence:
    print(item.term, item.ticket_quantities)

""" Example:
    [2026-04-27 01:39:19.986299+00:00, 2026-05-04 01:39:19.986299+00:00)  6
    [2026-05-04 01:39:19.986299+00:00, 2026-05-11 01:39:19.986299+00:00)  5
    [2026-05-11 01:39:19.986299+00:00, 2026-05-18 01:39:19.986299+00:00)  2
    [2026-05-18 01:39:19.986299+00:00, 2026-05-25 01:39:19.986299+00:00)  8
    [2026-05-25 01:39:19.986299+00:00, 2026-06-01 01:39:19.986299+00:00)  1
    [2026-06-01 01:39:19.986299+00:00, 2026-06-08 01:39:19.986299+00:00)  5
    [2026-06-08 01:39:19.986299+00:00, 2026-06-15 01:39:19.986299+00:00)  6
    [2026-06-15 01:39:19.986299+00:00, 2026-06-22 01:39:19.986299+00:00)  4
    [2026-06-22 01:39:19.986299+00:00, 2026-06-29 01:39:19.986299+00:00)  4
    [2026-06-29 01:39:19.986299+00:00, 2026-07-06 01:39:19.986299+00:00)  6
    [2026-07-06 01:39:19.986299+00:00, 2026-07-13 01:39:19.986299+00:00)  6
    [2026-07-13 01:39:19.986299+00:00, 2026-07-20 01:39:19.986299+00:00)  7
"""
```

The resulting SQL would look something like:

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
  ) AS "ticket_quantities"
FROM
  (
    --- 1
    SELECT
      tstzrange((lag(a) OVER()), a, '[)') AS term
    FROM
      generate_series(
        timestamptz '2026-04-27T01:39:19.986299+00:00' :: timestamptz,
        timestamptz '2026-07-26T01:39:19.986299+00:00' :: timestamptz,
        interval '7 days'
      ) AS a OFFSET 1
  ) AS django_generate_series_datetimerangefieldseries
ORDER BY
  "django_generate_series_datetimerangefieldseries"."term" ASC;
```

## Create a Histogram

This example is a slight modification of the example above, using the same Event model. Here we are creating histogram buckets with a size of 5, and counting how many events have a number of tickets that falls in a given bucket.

### Create some random events (similar to above, but using COUNT)

```python
import random
from datetime import timedelta
from django.contrib.postgres.fields import IntegerRangeField
from django.db import models
from django.db.models import OuterRef, Subquery, Count
from django.utils import timezone
from django_generate_series.models import generate_series

now = timezone.now()
SECONDS_IN_90_DAYS = 90 * 24 * 3600

for x in range(0, 30):
    # Create 30 Event instances with random datetime and a ticket_qty between 1 and 50
    random_dt = now + timedelta(seconds=random.randint(0, SECONDS_IN_90_DAYS))
    Event.objects.create(event_datetime=random_dt, ticket_qty=random.randrange(1, 50))

# Create a Subquery of annotated Event objects
for item in Event.objects.all().order_by("ticket_qty"):
    print(item.event_datetime, item.ticket_qty)

""" Example
    2026-07-15 04:05:55.832641+00:00  9
    2026-05-06 17:45:00.836057+00:00  12
    2026-05-07 16:28:26.833515+00:00  14
    2026-06-20 20:45:21.849374+00:00  15
    2026-05-08 22:15:01.856055+00:00  15
    2026-05-28 12:25:49.852562+00:00  19
    2026-05-14 20:17:00.831192+00:00  19
    2026-07-18 17:48:43.836904+00:00  19
    2026-07-11 01:49:23.843757+00:00  20
    2026-07-08 05:36:27.835197+00:00  21
    2026-05-27 18:56:23.855121+00:00  24
    2026-06-13 00:18:37.837913+00:00  25
    2026-05-17 11:24:04.854219+00:00  27
    2026-06-18 00:45:12.850166+00:00  28
    2026-05-04 16:59:48.842067+00:00  29
    2026-06-14 03:15:12.856889+00:00  31
    2026-06-13 23:03:33.846176+00:00  32
    2026-07-04 23:53:10.848583+00:00  33
    2026-06-09 19:31:38.846988+00:00  36
    2026-06-29 01:25:15.853390+00:00  37
    2026-05-03 13:23:10.845404+00:00  38
    2026-05-16 08:13:33.844641+00:00  39
    2026-05-30 08:54:01.841235+00:00  40
    2026-07-16 22:22:37.838889+00:00  41
    2026-06-12 16:21:05.851736+00:00  42
    2026-04-30 16:39:31.834378+00:00  43
    2026-06-22 03:38:17.842864+00:00  45
    2026-07-02 15:54:05.840007+00:00  45
    2026-07-04 18:12:47.850951+00:00  48
    2026-05-05 11:44:31.847756+00:00  49

"""

# Using Count instead of Sum
event_subquery = (
    Event.objects.filter(ticket_qty__contained_by=OuterRef("term"))
    .order_by()
    .annotate(count_of_tickets=Func(F("ticket_qty"), function="COUNT"))
    .values("count_of_tickets")
)
```

### Generate and annotate the datetime ranges

Here we create 10 buckets with a `step` (the difference from one term's lower bound to another term's lower bound) and `span` (the difference between the lower bound and upper bound of each term) of 5, from 1 to 50.

```python
datetime_range_sequence = (
    generate_series(start=0, stop=49, step=5, span=5, output_field=IntegerRangeField)
    .annotate(ticket_quantities=Subquery(event_subquery))
    .order_by("term")
)

for item in datetime_range_sequence:
    print(item.term, item.ticket_quantities)

""" Example:
    [0, 5)    None
    [5, 10)   1
    [10, 15)  2
    [15, 20)  5
    [20, 25)  3
    [25, 30)  4
    [30, 35)  3
    [35, 40)  4
    [40, 45)  4
    [45, 50)  4
"""
```

The resulting SQL would look something like:

```sql
SELECT
  "django_generate_series_integerrangefieldseries"."term",
  (
    SELECT
      COUNT(U0."ticket_qty") AS "count_of_tickets"
    FROM
      "core_event" U0
    WHERE
      U0."ticket_qty" < @ "django_generate_series_integerrangefieldseries"."term" :: int4range
  ) AS "ticket_quantities"
FROM
  (
    SELECT
      int4range(a, a + 5) AS term
    FROM
      generate_series(0, 49, 5) a
  ) AS django_generate_series_integerrangefieldseries
ORDER BY
  "django_generate_series_integerrangefieldseries"."term" ASC;
```

## Using an iterable with the series to get a cartesian product

In this example, we will create a sequence of integers from -12 to 12, stepping by 3, and combine each term with the values in the iterable `["A", "B", "C"]` to create a cartesian product.

```python
from django.db import models
from django_generate_series.models import generate_series

integer_sequence_with_cartesian_product = generate_series(
    start=-12,
    stop=12,
    step=3, 
    output_field=models.IntegerField, 
    iterable=["A", "B", "C"],
)

for item in integer_sequence_with_cartesian_product:
    print(item.term, item.value)

"""
Example output:
   term   value (iterable)
    -12   A
    -12   B
    -12   C
    -9    A
    -9    B
    -9    C
    -6    A
    -6    B
    -6    C
    -3    A
    -3    B
    -3    C
    ...  
     12   C
"""
```

Resulting SQL:  <!-- ToDo: Update this -->

```sql
SELECT 
  "django_generate_series_integerfieldseries"."term",
  "django_generate_series_integerfieldseries"."value" 
FROM 
  (
    WITH series AS (
      --- 3
      SELECT 
        generate_series(-12, 12, 3) term
    ), 
    iterable AS (
      SELECT 
        UNNEST(ARRAY[ 'A', 'B', 'C' ]) AS value
    ) 
    SELECT 
      series.term, 
      iterable.value 
    FROM 
      series, 
      iterable
  ) AS django_generate_series_integerfieldseries
```

## Using a QuerySet with the series to get a cartesian product

In this example, we will create a sequence of integers from -12 to 12, stepping by 3, and combine each term with the primary key of instances of a model `SomeModel` that meet a condition.

```python
from django.db import models
from django_generate_series.models import generate_series

# Assuming there are SimpleOrder instances (see model definition above)
simple_order_qs = SimpleOrder.objects.filter(cost__gte=20)

integer_sequence_with_cartesian_product = generate_series(
    start=-12,
    stop=12,
    step=3, 
    output_field=models.IntegerField, 
    queryset=simple_order_qs,
)

for item in integer_sequence_with_cartesian_product:
    print(item.term, item.value)

"""
Example output:
   term   value (pk of SimpleOrder instances)
    -12   2
     -9   2
     -6   2
     -3   2
      0   2
      3   2
      6   2
      9   2
     12   2
    -12   3
     -9   3
     -6   3
     -3   3
      0   3
      3   3
      6   3
      9   3
     12   3
    ...  
     12   30
"""
```

Resulting SQL:

```sql
SELECT
    "django_generate_series_integerfieldseries"."term"
	,"django_generate_series_integerfieldseries"."value"
FROM (
	WITH series AS (
			--- NULL
			SELECT generate_series(- 12, 12, 3) term
			)
		,queryset_pks AS (
			SELECT "core_simpleorder"."id"
			FROM "core_simpleorder"
			WHERE "core_simpleorder"."cost" >= 20
			)
	SELECT series.term
		,queryset_pks.id AS value
	FROM series
		,queryset_pks
	) AS django_generate_series_integerfieldseries
```

## Create a set of Histograms using an Iterable with the series to get a cartesian product

This example is a slight modification of the `Create a Histogram` example above, using the same Event model. Here we are creating histogram buckets with a size of 5, and counting how many events have a number of tickets that falls in a given bucket, and then combining each term of the histogram with the values in the iterable `["A", "B", "C"]` to create a cartesian product.

```python
import random
from datetime import timedelta
from django.contrib.postgres.fields import IntegerRangeField
from django.db import models
from django.db.models import OuterRef, Subquery, Count, F, Func
from django.utils import timezone
from django_generate_series.models import generate_series

now = timezone.now()
SECONDS_IN_90_DAYS = 90 * 24 * 3600

for x in range(0, 30):
    # Create 30 Event instances with random datetime and a ticket_qty between 1 and 50
    random_dt = now + timedelta(seconds=random.randint(0, SECONDS_IN_90_DAYS))
    Event.objects.create(event_datetime=random_dt, ticket_qty=random.randrange(1, 50))

# Create a Subquery of annotated Event objects
event_subquery = (
    Event.objects.filter(ticket_qty__contained_by=OuterRef("term"))
    .order_by()
    .annotate(count_of_tickets=Func(F("ticket_qty"), function="COUNT"))
    .values("count_of_tickets")
)

# Using Count instead of Sum
histogram_sequence_with_cartesian_product = generate_series(
    start=0,
    stop=49,
    step=5,
    span=5,
    output_field=IntegerRangeField,
    iterable=["A", "B", "C"],
).annotate(ticket_quantities=Subquery(event_subquery))

for item in histogram_sequence_with_cartesian_product:
    print(item.term, item.ticket_quantities, item.value)

""" Example:
    [0, 5)    None  A
    [0, 5)    None  B
    [0, 5)    None  C
    [5, 10)   1     A
    [5, 10)   1     B
    [5, 10)   1     C
    [10, 15)  2     A
    [10, 15)  2     B
    [10, 15)  2     C
    [15, 20)  5     A
    [15, 20)  5     B
    [15, 20)  5     C
    [20, 25)  3     A
    [20, 25)  3     B
    [20, 25)  3     C
    [25, 30)  4     A
    [25, 30)  4     B
    [25, 30)  4     C
    [30, 35)  3     A
    [30, 35)  3     B
    [30, 35)  3     C
    [35, 40)  4     A
    [35, 40)  4     B
    [35, 40)  4     C
    [40, 45)  4     A
    [40, 45)  4     B
    [40, 45)  4     C
    [45, 50)  4     A
    [45, 50)  4     B
    [45, 50)  4     C
"""
```

Resulting SQL:  <!-- ToDo: Update this -->

```sql
SELECT "django_generate_series_integerrangefieldseries"."term"
	,"django_generate_series_integerrangefieldseries"."value"
	,(
		SELECT COUNT(U0."ticket_qty") AS "count_of_tickets"
		FROM "core_event" U0
		WHERE U0."ticket_qty" < @("django_generate_series_integerrangefieldseries"."term")::int4range
		) AS "ticket_quantities"
FROM (
	WITH series AS (
			SELECT int4range(a, a + 5) AS term
			FROM generate_series(0, 49, 5) a
			)
		,iterable AS (
			SELECT UNNEST(ARRAY ['A','B','C']) AS value
			)
	SELECT series.term
		,iterable.value
	FROM series
		,iterable
	) AS django_generate_series_integerrangefieldseries
```

## Create a set of Histograms using a QuerySet with the series to get a cartesian product

This example is a slight modification of the `Create a Histogram` example above, using the same Event model. Here we are creating histogram buckets with a size of 5, and counting how many events have a number of tickets that falls in a given bucket, and then combining each term of the histogram with the primary key of instances of a model `SomeModel` that meet a condition.

For the examle output, we are assuming that `SomeModel` is a model in your app with three instances (with `pk` of 1, 2, and 3) that meet the condition `some_condition=True`.

```python
import random
from datetime import timedelta
from django.contrib.postgres.fields import IntegerRangeField
from django.db import models
from django.db.models import OuterRef, Subquery, Count, F, Func
from django.utils import timezone
from django_generate_series.models import generate_series

now = timezone.now()
SECONDS_IN_90_DAYS = 90 * 24 * 3600

for x in range(0, 30):
    # Create 30 Event instances with random datetime and a ticket_qty between 1 and 50
    random_dt = now + timedelta(seconds=random.randint(0, SECONDS_IN_90_DAYS))
    Event.objects.create(event_datetime=random_dt, ticket_qty=random.randrange(1, 50))

# Create a Subquery of annotated Event objects
event_subquery = (
    Event.objects.filter(ticket_qty__contained_by=OuterRef("term"))
    .order_by()
    .annotate(count_of_tickets=Func(F("ticket_qty"), function="COUNT"))
    .values("count_of_tickets")
)

# Using Count instead of Sum
histogram_sequence_with_cartesian_product = generate_series(
    start=0,
    stop=49,
    step=5,
    span=5,
    output_field=IntegerRangeField,
    queryset=SimpleOrder.objects.filter(cost__gte=20),
)


for item in histogram_sequence_with_cartesian_product:
    print(item.term, item.ticket_quantities, item.value)

""" Example:
    [0, 5)    None  1
    [0, 5)    None  2
    [0, 5)    None  3
    [5, 10)   1     1
    [5, 10)   1     2
    [5, 10)   1     3
    [10, 15)  2     1
    [10, 15)  2     2
    [10, 15)  2     3
    [15, 20)  5     1
    [15, 20)  5     2
    [15, 20)  5     3
    [20, 25)  3     1
    [20, 25)  3     2
    [20, 25)  3     3
    [25, 30)  4     1
    [25, 30)  4     2
    [25, 30)  4     3
    [30, 35)  3     1
    [30, 35)  3     2
    [30, 35)  3     3
    [35, 40)  4     1
    [35, 40)  4     2
    [35, 40)  4     3
    [40, 45)  4     1
    [40, 45)  4     2
    [40, 45)  4     3
    [45, 50)  4     1
    [45, 50)  4     2
    [45, 50)  4     3
"""
```

Resulting SQL:  <!-- ToDo: Update this -->

```sql
WITH series AS (
    SELECT int4range(a, a + 5) AS term
    FROM generate_series(0, 49, 5) a
),
queryset_pks AS (
    SELECT "some_model"."id" AS pk
    FROM "some_model"
    WHERE "some_model"."some_condition" = True
)
SELECT series.term, queryset_pks.pk
FROM series, queryset_pks;
```

