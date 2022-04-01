import logging

from django.db import models

logger = logging.getLogger("django_generate_series")


class NoEffectQuerySet(models.QuerySet):
    def log_no_effect_method_warning(self):
        logger.warning(
            "This model has been intentionally limited in capability. "
            "The requested method has no effect and will be ignored."
        )

    def delete(self):
        self.log_no_effect_method_warning()
        return self


class NoEffectManager(models.Manager):
    def log_no_effect_method_warning(self):
        logger.warning(
            "This model has been intentionally limited in capability. "
            "Until a series has been generated, the requested method has no effect."
        )

    def filter(self):
        self.log_no_effect_method_warning()
        return self

    def exclude(self):
        self.log_no_effect_method_warning()
        return self

    def annotate(self):
        self.log_no_effect_method_warning()
        return self

    def alias(self):
        self.log_no_effect_method_warning()
        return self

    def order_by(self):
        self.log_no_effect_method_warning()
        return self

    def reverse(self):
        self.log_no_effect_method_warning()
        return self

    def distinct(self):
        self.log_no_effect_method_warning()
        return self

    def values(self):
        self.log_no_effect_method_warning()
        return self

    def values_list(self):
        self.log_no_effect_method_warning()
        return self

    def dates(self):
        self.log_no_effect_method_warning()
        return self

    def datetimes(self):
        self.log_no_effect_method_warning()
        return self

    def none(self):
        self.log_no_effect_method_warning()
        return self

    def all(self):
        self.log_no_effect_method_warning()
        return self

    def union(self):
        self.log_no_effect_method_warning()
        return self

    def intersection(self):
        self.log_no_effect_method_warning()
        return self

    def difference(self):
        self.log_no_effect_method_warning()
        return self

    def select_related(self):
        self.log_no_effect_method_warning()
        return self

    def prefetch_related(self):
        self.log_no_effect_method_warning()
        return self

    def extra(self):
        self.log_no_effect_method_warning()
        return self

    def defer(self):
        self.log_no_effect_method_warning()
        return self

    def only(self):
        self.log_no_effect_method_warning()
        return self

    def using(self):
        self.log_no_effect_method_warning()
        return self

    def select_for_update(self):
        self.log_no_effect_method_warning()
        return self

    def raw(self):
        self.log_no_effect_method_warning()
        return self

    def get(self):
        self.log_no_effect_method_warning()
        return self

    def create(self):
        self.log_no_effect_method_warning()
        return self

    def get_or_create(self):
        self.log_no_effect_method_warning()
        return self

    def update_or_create(self):
        self.log_no_effect_method_warning()
        return self

    def bulk_create(self):
        self.log_no_effect_method_warning()
        return self

    def bulk_update(self):
        self.log_no_effect_method_warning()
        return self

    def count(self):
        self.log_no_effect_method_warning()
        return self

    def in_bulk(self):
        self.log_no_effect_method_warning()
        return self

    def iterator(self):
        self.log_no_effect_method_warning()
        return self

    def latest(self):
        self.log_no_effect_method_warning()
        return self

    def earliest(self):
        self.log_no_effect_method_warning()
        return self

    def first(self):
        self.log_no_effect_method_warning()
        return self

    def last(self):
        self.log_no_effect_method_warning()
        return self

    def aggregate(self):
        self.log_no_effect_method_warning()
        return self

    def exists(self):
        self.log_no_effect_method_warning()
        return self

    def contains(self):
        self.log_no_effect_method_warning()
        return self

    def update(self):
        self.log_no_effect_method_warning()
        return self

    def delete(self):
        self.log_no_effect_method_warning()
        return self

    def as_manager(self):
        self.log_no_effect_method_warning()
        return self

    def explain(self):
        self.log_no_effect_method_warning()
        return self
