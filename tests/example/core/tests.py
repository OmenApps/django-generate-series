import pytest
from django.conf import settings


def test_account_is_configured():
    assert "tests.example.core" in settings.INSTALLED_APPS
