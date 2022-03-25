import logging

from django.contrib.postgres.fields import DateRangeField, DateTimeRangeField
from django.db import models
from django.db.models.sql import Query

from django_generate_series.models import get_series_model

logger = logging.getLogger("django_generate_series")


class MyTest(get_series_model(models.IntegerField)):
    pass
