"""Service khởi tạo tài khoản admin từ cấu hình .env."""

from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from core.enums.user_role import UserRole


@dataclass
class AdminInitResult:
    """Kết quả khởi tạo/đồng bộ admin."""

    success: bool
    message: str
    created: bool = False
    user: Optional[User] = None


class AdminInitService:
    """Tạo hoặc đồng bộ admin — toàn bộ thông tin lấy từ .env qua settings."""

    @staticmethod
    def get_config() -> dict:
        """Đọc cấu hình admin từ settings (đã nạp từ .env)."""
        return {
            'username': settings.INIT_ADMIN_USERNAME.strip(),
            'email': settings.INIT_ADMIN_EMAIL.strip().lower(),
            'password': settings.INIT_ADMIN_PASSWORD,
            'full_name': settings.INIT_ADMIN_FULL_NAME.strip(),
        }

    @staticmethod
    def ensure_admin(sync: bool = False) -> AdminInitResult:
        """
        Đảm bảo tài khoản admin tồn tại.
        - Chưa có: tạo mới với role admin.
        - Đã có: bỏ qua hoặc đồng bộ lại từ .env nếu sync=True.
        """
        if not settings.INIT_ADMIN_ENABLED:
            return AdminInitResult(
                success=True,
                message='Bỏ qua khởi tạo admin (INIT_ADMIN_ENABLED=False).',
            )

        config = AdminInitService.get_config()
        username = config['username']
        email = config['email']
        password = config['password']
        full_name = config['full_name']

        if not username:
            return AdminInitResult(False, 'INIT_ADMIN_USERNAME không được để trống.')
        if not email:
            return AdminInitResult(False, 'INIT_ADMIN_EMAIL không được để trống.')
        if len(password) < 6:
            return AdminInitResult(False, 'INIT_ADMIN_PASSWORD phải có ít nhất 6 ký tự.')

        existing = User.objects.filter(username=username).first()
        if existing:
            if sync:
                return AdminInitService._sync_existing_admin(existing, config)
            return AdminInitResult(
                success=True,
                message=f'Tài khoản admin "{username}" đã tồn tại.',
                user=existing,
            )

        if UserRepository.email_exists(email):
            return AdminInitResult(
                False,
                f'Email "{email}" đã được sử dụng bởi tài khoản khác.',
            )

        user = UserRepository.create_user(
            username=username,
            email=email,
            password=PasswordService.hash_password(password),
            full_name=full_name or None,
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        return AdminInitResult(
            success=True,
            message=f'Đã tạo tài khoản admin "{username}".',
            created=True,
            user=user,
        )

    @staticmethod
    def _sync_existing_admin(user: User, config: dict) -> AdminInitResult:
        """Cập nhật admin hiện có theo .env — dùng khi đổi mật khẩu/email trong .env."""
        email = config['email']
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return AdminInitResult(
                False,
                f'Email "{email}" đã được sử dụng bởi tài khoản khác.',
            )

        user.email = email
        user.password = PasswordService.hash_password(config['password'])
        user.full_name = config['full_name'] or None
        user.role = UserRole.ADMIN.value
        user.is_active = True
        UserRepository.save(user)

        return AdminInitResult(
            success=True,
            message=f'Đã đồng bộ tài khoản admin "{user.username}" từ .env.',
            user=user,
        )
