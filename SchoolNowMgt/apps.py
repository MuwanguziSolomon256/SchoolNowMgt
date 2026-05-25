from django.apps import AppConfig


class SchoolnowmgtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SchoolNowMgt'
    verbose_name = 'School Management System'

    def ready(self):
        """Import signal receivers when the app is ready."""
        import SchoolNowMgt.signals  # noqa: F401
