"""Repository bảng system_logs và api_request_logs."""

from apps.monitoring.models import ApiRequestLog, SystemLog


class SystemLogRepository:
    """Truy vấn system_logs."""

    @staticmethod
    def create(**kwargs) -> SystemLog:
        return SystemLog.objects.create(**kwargs)

    @staticmethod
    def list_recent(level: str = '', source: str = '', limit: int = 100):
        qs = SystemLog.objects.all().order_by('-created_at')
        if level:
            qs = qs.filter(level=level)
        if source:
            qs = qs.filter(source__icontains=source)
        return qs[:limit]

    @staticmethod
    def count_errors():
        from core.enums.log_level import LogLevel
        return SystemLog.objects.filter(level=LogLevel.ERROR.value).count()


class ApiRequestLogRepository:
    """Truy vấn api_request_logs."""

    @staticmethod
    def create(**kwargs) -> ApiRequestLog:
        return ApiRequestLog.objects.create(**kwargs)

    @staticmethod
    def list_recent(slow_only: bool = False, path_contains: str = '', limit: int = 100):
        from django.conf import settings

        qs = ApiRequestLog.objects.select_related('user').order_by('-created_at')
        if slow_only:
            threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
            qs = qs.filter(execution_time_ms__gte=threshold)
        if path_contains:
            qs = qs.filter(path__icontains=path_contains)
        return qs[:limit]

    @staticmethod
    def count_slow():
        from django.conf import settings
        threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
        return ApiRequestLog.objects.filter(execution_time_ms__gte=threshold).count()

    @staticmethod
    def avg_execution_time():
        from django.db.models import Avg
        result = ApiRequestLog.objects.aggregate(v=Avg('execution_time_ms'))
        return result['v']
