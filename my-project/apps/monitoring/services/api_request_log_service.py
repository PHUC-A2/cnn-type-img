"""Ghi log HTTP request — api_request_logs."""

from django.http import HttpRequest, HttpResponse

from apps.monitoring.repositories.log_repository import ApiRequestLogRepository


class ApiRequestLogService:
    """Service lưu request log."""

    @staticmethod
    def _resolve_ip(request: HttpRequest) -> str:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '') or ''

    @staticmethod
    def _resolve_endpoint(request: HttpRequest) -> str:
        match = getattr(request, 'resolver_match', None)
        if match and match.view_name:
            return match.view_name
        return ''

    @staticmethod
    def should_skip(request: HttpRequest) -> bool:
        """Bỏ qua static/media — giảm noise."""
        path = request.path
        if path.startswith('/static/') or path.startswith('/media/'):
            return True
        return False

    @staticmethod
    def log_request(request: HttpRequest, response: HttpResponse, execution_time_ms: float) -> None:
        """Lưu bản ghi request."""
        user = getattr(request, 'user', None)
        user_obj = user if getattr(user, 'is_authenticated', False) else None

        try:
            ApiRequestLogRepository.create(
                method=request.method,
                path=request.path[:500],
                endpoint=ApiRequestLogService._resolve_endpoint(request)[:200],
                status_code=response.status_code,
                execution_time_ms=round(execution_time_ms, 2),
                ip_address=ApiRequestLogService._resolve_ip(request),
                user=user_obj,
            )
        except Exception:
            pass

        from django.conf import settings
        threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 1000)
        if execution_time_ms >= threshold:
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.warning(
                'middleware',
                f'Request chậm: {request.method} {request.path} — {execution_time_ms:.1f}ms',
                context={
                    'status_code': response.status_code,
                    'endpoint': ApiRequestLogService._resolve_endpoint(request),
                },
            )

        if response.status_code >= 500:
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.error(
                'middleware',
                f'HTTP {response.status_code}: {request.method} {request.path}',
                context={'status_code': response.status_code},
            )
