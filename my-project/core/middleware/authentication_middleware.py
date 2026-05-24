"""Middleware gắn user vào request từ signed cookie."""

from apps.authentication.services.session_service import SessionService


class AuthenticationMiddleware:
    """Middleware custom auth — không dùng django.contrib.auth."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        SessionService.attach_user(request)
        return self.get_response(request)
