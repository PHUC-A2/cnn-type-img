from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from core.enums.user_role import UserRole


def login_required(view_func):
    """Decorator — bắt buộc đăng nhập mới truy cập view."""

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return redirect('authentication:login')
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Decorator — chỉ role admin mới truy cập."""

    @wraps(view_func)
    @login_required
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if request.user.role != UserRole.ADMIN.value:
            return redirect('authentication:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper
