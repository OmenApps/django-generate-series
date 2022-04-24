import warnings

from django.db import models


def _warn_no_effect(self, *args, **kwargs):
    warnings.warn(
        "This model has been intentionally limited in capability. "
        "The requested method has no effect and will be ignored.",
        stacklevel=2,
    )
    return self


class NoEffectQuerySet(models.QuerySet):
    delete = _warn_no_effect


class NoEffectManager(models.Manager):
    filter = _warn_no_effect
    exclude = _warn_no_effect
    annotate = _warn_no_effect
    alias = _warn_no_effect
    order_by = _warn_no_effect
    reverse = _warn_no_effect
    distinct = _warn_no_effect
    values = _warn_no_effect
    values_list = _warn_no_effect
    dates = _warn_no_effect
    datetimes = _warn_no_effect
    none = _warn_no_effect
    all = _warn_no_effect
    union = _warn_no_effect
    intersection = _warn_no_effect
    difference = _warn_no_effect
    select_related = _warn_no_effect
    prefetch_related = _warn_no_effect
    extra = _warn_no_effect
    defer = _warn_no_effect
    only = _warn_no_effect
    using = _warn_no_effect
    select_for_update = _warn_no_effect
    raw = _warn_no_effect
    get = _warn_no_effect
    create = _warn_no_effect
    get_or_create = _warn_no_effect
    update_or_create = _warn_no_effect
    bulk_create = _warn_no_effect
    bulk_update = _warn_no_effect
    count = _warn_no_effect
    in_bulk = _warn_no_effect
    iterator = _warn_no_effect
    latest = _warn_no_effect
    earliest = _warn_no_effect
    first = _warn_no_effect
    last = _warn_no_effect
    aggregate = _warn_no_effect
    exists = _warn_no_effect
    contains = _warn_no_effect
    update = _warn_no_effect
    delete = _warn_no_effect
    as_manager = _warn_no_effect
    explain = _warn_no_effect
