"""Service nghiệp vụ đăng ký, đăng nhập, cập nhật profile."""

from dataclasses import dataclass
from typing import Optional

from django.utils import timezone

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from core.enums.user_role import UserRole


@dataclass
class AuthResult:
    """Kết quả trả về từ service auth."""

    success: bool
    message: str
    user: Optional[User] = None


class AuthService:
    """Xử lý logic auth — view chỉ gọi service này."""

    @staticmethod
    def register(
        username: str,
        email: str,
        password: str,
        full_name: str = '',
    ) -> AuthResult:
        username = username.strip()
        email = email.strip().lower()
        full_name = full_name.strip()

        if len(username) < 3:
            return AuthResult(False, 'Tên đăng nhập phải có ít nhất 3 ký tự.')
        if len(password) < 6:
            return AuthResult(False, 'Mật khẩu phải có ít nhất 6 ký tự.')
        if UserRepository.username_exists(username):
            return AuthResult(False, 'Tên đăng nhập đã tồn tại.')
        if UserRepository.email_exists(email):
            return AuthResult(False, 'Email đã được sử dụng.')

        user = UserRepository.create_user(
            username=username,
            email=email,
            password=PasswordService.hash_password(password),
            full_name=full_name or None,
            role=UserRole.USER.value,
            is_active=True,
        )
        return AuthResult(True, 'Đăng ký thành công.', user)

    @staticmethod
    def login(username: str, password: str) -> AuthResult:
        username = username.strip()
        user = UserRepository.get_by_username(username)
        if not user:
            # Thử tìm theo email
            user = UserRepository.get_by_email(username.lower())

        if not user or not PasswordService.verify_password(password, user.password):
            return AuthResult(False, 'Tên đăng nhập hoặc mật khẩu không đúng.')

        user.last_login = timezone.now()
        UserRepository.save(user)
        return AuthResult(True, 'Đăng nhập thành công.', user)

    @staticmethod
    def update_profile(user: User, full_name: str, email: str) -> AuthResult:
        email = email.strip().lower()
        full_name = full_name.strip()

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return AuthResult(False, 'Email đã được sử dụng bởi tài khoản khác.')

        user.full_name = full_name or None
        user.email = email
        UserRepository.save(user)
        return AuthResult(True, 'Cập nhật hồ sơ thành công.', user)

    @staticmethod
    def update_avatar(user: User, avatar_url: str) -> AuthResult:
        user.avatar_url = avatar_url
        UserRepository.save(user)
        return AuthResult(True, 'Cập nhật avatar thành công.', user)
