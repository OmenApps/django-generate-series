from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_superuser(sender, **kwargs):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if not User.objects.filter(username="admin", email="admin@example.com").exists():
        User.objects.create_superuser("admin", "admin@example.com", "pass")


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.example.core"

    def ready(self) -> None:
        post_migrate.connect(create_superuser, sender=self)
