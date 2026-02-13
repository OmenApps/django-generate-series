"""Settings for the django-generate-series."""

from django.conf import settings

# Namespaced dictionary for the settings.
DJANGO_GENERATE_SERIES = getattr(settings, "DJANGO_GENERATE_SERIES", {})

DGS_DEFAULT_AUTO_FIELD = DJANGO_GENERATE_SERIES.get(
    "DEFAULT_AUTO_FIELD", getattr(settings, "DEFAULT_AUTO_FIELD", "django.db.models.AutoField")
)
"""Default auto field for the generate_series function.

If not set, it will use the default auto field from the settings.
"""

DGS_DEFAULT_AUTO_FIELD_DEFAULT_CALLABLE = DJANGO_GENERATE_SERIES.get("DEFAULT_AUTO_FIELD_DEFAULT_CALLABLE", None)
"""Default callable for the default value of the auto field.

Used if, for instance, the auto field is a UUID field.

Example: `uuid.uuid4`

If not set, no default callable will be used.
"""
