"""Service quản lý session đăng nhập qua signed cookie."""

from typing import Any, Optional

from django.conf import settings
from django.core import signing
from django.http import HttpResponse

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository


class AnonymousUser:
    """User ẩn danh — chưa đăng nhập."""

    is_authenticated = False
    is_admin = False
    role = None
    username = ''
    id = None

    def get_display_name(self) -> str:
        return 'Khách'


class SessionService:
    """Tạo/đọc/xóa session auth bằng signed cookie — không dùng bảng django_session."""

    SALT = 'cnn-auth-session-v1'

    @classmethod
    def attach_user(cls, request) -> None:
        """Gắn request.user từ cookie session."""
        user = cls.get_user_from_request(request)
        request.user = user if user else AnonymousUser()

    @classmethod
    def get_user_from_request(cls, request) -> Optional[User]:
        cookie_value = request.COOKIES.get(settings.AUTH_COOKIE_NAME)
        if not cookie_value:
            return None
        try:
            payload = signing.loads(
                cookie_value,
                salt=cls.SALT,
                max_age=settings.AUTH_REMEMBER_MAX_AGE,
            )
            user_id = payload.get('user_id')
            if not user_id:
                return None
            return UserRepository.get_by_id(int(user_id))
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            return None

    @classmethod
    def login(cls, response: HttpResponse, user: User, remember_me: bool = False) -> HttpResponse:
        """Ghi cookie session sau khi đăng nhập thành công."""
        max_age = settings.AUTH_REMEMBER_MAX_AGE if remember_me else settings.AUTH_SESSION_MAX_AGE
        payload: dict[str, Any] = {'user_id': user.id, 'remember': remember_me}
        signed = signing.dumps(payload, salt=cls.SALT)
        response.set_cookie(
            settings.AUTH_COOKIE_NAME,
            signed,
            max_age=max_age,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG,
        )
        return response

    @classmethod
    def logout(cls, response: HttpResponse) -> HttpResponse:
        """Xóa cookie session khi đăng xuất."""
        response.delete_cookie(settings.AUTH_COOKIE_NAME)
        return response
