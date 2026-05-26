"""App monitoring — admin panel Phase 8–9."""

from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.monitoring'
    verbose_name = 'Quản trị hệ thống'

    def ready(self):
        from core.logging.loguru_config import setup_loguru
        setup_loguru()
