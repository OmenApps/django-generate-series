from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor


def is_database_synchronized(database):
    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return not executor.migration_plan(targets)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.example.core"

    def ready(self) -> None:
        if is_database_synchronized(DEFAULT_DB_ALIAS):
            User = get_user_model()
            user_exists = User.objects.filter(username="admin", email="admin@example.com").exists()
            if not user_exists:
                User.objects.create_superuser("admin", "admin@example.com", "pass")
