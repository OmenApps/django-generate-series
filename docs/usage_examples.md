# Usage Examples

## Get the order costs for orders placed every other day over the past month

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
previous = (now - timezone.timedelta(days=30))

def random_date_in_past_month():
    # Generate a radom date within the past 30 days
    return get_random_date(min_date=previous, max_timedelta=timezone.timedelta(days=30))

for x in range(0, 30):
    # Create 30 SimpleOrder instances with random date and a cost between $1 and $50
    SimpleOrder.objects.create(order_date=random_date_in_past_month(), cost=random.randrange(1, 50))

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
