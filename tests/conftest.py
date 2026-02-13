"""Shared pytest fixtures for django-generate-series tests."""

import pytest

from tests.example.core.sequence_utils import get_date_sequence, get_datetime_sequence


@pytest.fixture
def date_sequence():
    """Generate a tuple of 10 sequential dates starting from today."""
    return tuple(get_date_sequence())


@pytest.fixture
def datetime_sequence():
    """Generate a tuple of 10 sequential datetimes starting from now."""
    return tuple(get_datetime_sequence())
