"""Sphinx configuration."""

import django
from django.conf import settings


settings.configure(DEBUG=True)

# Initialize Django
django.setup()

project = "django-generate-series"
author = "Jack Linke"
copyright = "2024, Jack Linke"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
