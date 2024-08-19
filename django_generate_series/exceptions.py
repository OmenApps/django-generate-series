"""Custom exceptions for the django_generate_series app."""


class ModelFieldNotSupported(Exception):
    """The selected base model field is not supported."""


class InvalidStepValue(Exception):
    """If provided as a string, the step value must be a valid numeric value, a space, and a valid interval type."""


class InvalidIntervalUnit(Exception):
    """The provided interval unit is not valid."""
