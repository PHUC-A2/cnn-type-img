"""Models logging — system_logs, api_request_logs."""

from django.db import models

from apps.authentication.models import User
from core.enums.log_level import LogLevel


class SystemLog(models.Model):
    """Log hệ thống — lỗi, cảnh báo, sự kiện training/prediction."""

    level = models.CharField(
        max_length=20,
        choices=LogLevel.choices(),
        default=LogLevel.INFO.value,
        verbose_name='Mức độ',
    )
    source = models.CharField(max_length=100, verbose_name='Nguồn')
    message = models.TextField(verbose_name='Nội dung')
    stack_trace = models.TextField(blank=True, null=True, verbose_name='Stack trace')
    context_json = models.JSONField(blank=True, null=True, verbose_name='Context')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    class Meta:
        db_table = 'system_logs'
        verbose_name = 'Log hệ thống'
        verbose_name_plural = 'Log hệ thống'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'[{self.level}] {self.source}: {self.message[:60]}'

    def get_level_display_vi(self) -> str:
        try:
            return LogLevel(self.level).label_vi()
        except ValueError:
            return self.level


class ApiRequestLog(models.Model):
    """Log HTTP request — endpoint, status, thời gian xử lý, IP."""

    method = models.CharField(max_length=10, verbose_name='Method')
    path = models.CharField(max_length=500, verbose_name='Đường dẫn')
    endpoint = models.CharField(max_length=200, blank=True, null=True, verbose_name='Endpoint')
    status_code = models.IntegerField(verbose_name='Status')
    execution_time_ms = models.FloatField(verbose_name='Thời gian (ms)')
    ip_address = models.CharField(max_length=45, blank=True, null=True, verbose_name='IP')
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_column='user_id',
        related_name='api_request_logs',
        verbose_name='Người dùng',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')

    class Meta:
        db_table = 'api_request_logs'
        verbose_name = 'Log request'
        verbose_name_plural = 'Log request'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.method} {self.path} — {self.status_code} ({self.execution_time_ms:.1f}ms)'

    @property
    def is_slow(self) -> bool:
        from django.conf import settings
        return self.execution_time_ms >= getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
