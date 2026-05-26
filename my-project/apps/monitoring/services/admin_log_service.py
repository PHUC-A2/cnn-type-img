"""Dashboard log — error + slow request panel."""

from dataclasses import dataclass
from typing import Optional

from django.db.models import Avg

from apps.monitoring.models import ApiRequestLog, SystemLog
from apps.monitoring.services.admin_pagination_service import AdminPaginationService
from core.enums.log_level import LogLevel


@dataclass
class LogDashboardStats:
    """Thống kê tổng quan trang logs."""

    total_system_logs: int
    error_count: int
    warning_count: int
    total_requests: int
    slow_request_count: int
    avg_latency_ms: Optional[float]
    cpu_percent: Optional[float]
    memory_percent: Optional[float]


class AdminLogService:
    """Truy vấn log cho admin panel."""

    @staticmethod
    def get_system_stats() -> tuple[Optional[float], Optional[float]]:
        """CPU/RAM hiện tại — optional psutil."""
        try:
            import psutil
            return round(psutil.cpu_percent(interval=0.1), 1), round(psutil.virtual_memory().percent, 1)
        except ImportError:
            return None, None

    @staticmethod
    def build_stats() -> LogDashboardStats:
        from django.conf import settings

        threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
        cpu, mem = AdminLogService.get_system_stats()
        avg = ApiRequestLog.objects.aggregate(v=Avg('execution_time_ms'))['v']

        return LogDashboardStats(
            total_system_logs=SystemLog.objects.count(),
            error_count=SystemLog.objects.filter(level=LogLevel.ERROR.value).count(),
            warning_count=SystemLog.objects.filter(level=LogLevel.WARNING.value).count(),
            total_requests=ApiRequestLog.objects.count(),
            slow_request_count=ApiRequestLog.objects.filter(execution_time_ms__gte=threshold).count(),
            avg_latency_ms=round(float(avg), 2) if avg is not None else None,
            cpu_percent=cpu,
            memory_percent=mem,
        )

    @staticmethod
    def list_system_logs(level: str = '', source: str = '', page: int = 1):
        qs = SystemLog.objects.all().order_by('-created_at')
        if level:
            qs = qs.filter(level=level)
        if source:
            qs = qs.filter(source__icontains=source.strip())
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def list_request_logs(slow_only: bool = False, path: str = '', page: int = 1):
        from django.conf import settings

        qs = ApiRequestLog.objects.select_related('user').order_by('-created_at')
        if slow_only:
            threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
            qs = qs.filter(execution_time_ms__gte=threshold)
        if path:
            qs = qs.filter(path__icontains=path.strip())
        return AdminPaginationService.paginate(qs, page=page)
