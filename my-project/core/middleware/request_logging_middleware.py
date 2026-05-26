"""Middleware ghi log mọi HTTP request."""

import time

from django.http import HttpRequest, HttpResponse

from apps.monitoring.services.api_request_log_service import ApiRequestLogService
from apps.monitoring.services.system_log_service import SystemLogService


class RequestLoggingMiddleware:
    """Ghi endpoint, status, execution time, IP vào api_request_logs."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if ApiRequestLogService.should_skip(request):
            return self.get_response(request)

        started = time.perf_counter()
        try:
            response = self.get_response(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            SystemLogService.error(
                'middleware',
                f'Unhandled exception: {request.method} {request.path}',
                exc=exc,
                context={'execution_time_ms': round(elapsed_ms, 2)},
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        ApiRequestLogService.log_request(request, response, elapsed_ms)
        return response
