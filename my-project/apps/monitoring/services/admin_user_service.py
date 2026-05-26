"""CRUD người dùng — admin panel."""

from dataclasses import dataclass
from typing import Optional

from django.db.models import Q

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.authentication.validators import validate_email_format, validate_username_format
from apps.monitoring.services.admin_pagination_service import AdminPaginationService
from core.enums.user_role import UserRole


@dataclass
class AdminActionResult:
    """Kết quả thao tác admin."""

    success: bool
    message: str


@dataclass
class AdminUserDetailView:
    """DTO chi tiết người dùng — admin panel."""

    user: User
    dataset_count: int
    model_count: int
    training_job_count: int
    prediction_count: int


class AdminUserService:
    """Quản lý user toàn hệ thống."""

    @staticmethod
    def list_users(q: str = '', include_inactive: bool = True, page: int = 1):
        qs = UserRepository.list_all(include_inactive=include_inactive)
        if q:
            keyword = q.strip()
            qs = qs.filter(
                Q(username__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(full_name__icontains=keyword)
            )
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def get_user_detail(user_id: int) -> Optional[AdminUserDetailView]:
        """Lấy thông tin chi tiết + thống kê hoạt động của user."""
        user = UserRepository.get_by_id_any(user_id)
        if not user:
            return None
        return AdminUserDetailView(
            user=user,
            dataset_count=user.datasets.count(),
            model_count=user.cnn_models.count(),
            training_job_count=user.training_jobs.count(),
            prediction_count=user.predictions.count(),
        )

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        full_name: str = '',
        role: str = UserRole.USER.value,
    ) -> AdminActionResult:
        username = username.strip()
        email = email.strip().lower()
        full_name = full_name.strip()

        if len(username) < 3:
            return AdminActionResult(False, 'Tên đăng nhập phải có ít nhất 3 ký tự.')
        if not validate_username_format(username):
            return AdminActionResult(False, 'Tên đăng nhập không hợp lệ.')
        if not validate_email_format(email):
            return AdminActionResult(False, 'Email không hợp lệ.')
        if len(password) < 6:
            return AdminActionResult(False, 'Mật khẩu phải có ít nhất 6 ký tự.')
        if UserRepository.username_exists(username):
            return AdminActionResult(False, 'Tên đăng nhập đã tồn tại.')
        if UserRepository.email_exists(email):
            return AdminActionResult(False, 'Email đã được sử dụng.')
        if role not in {UserRole.ADMIN.value, UserRole.USER.value}:
            return AdminActionResult(False, 'Vai trò không hợp lệ.')

        UserRepository.create_user(
            username=username,
            email=email,
            password=PasswordService.hash_password(password),
            full_name=full_name or None,
            role=role,
            is_active=True,
        )
        return AdminActionResult(True, 'Tạo người dùng thành công.')

    @staticmethod
    def update_user(
        user_id: int,
        username: str,
        full_name: str,
        role: str,
        is_active: bool,
        new_password: str = '',
        actor: Optional[User] = None,
    ) -> AdminActionResult:
        """Cập nhật user — email không đổi qua admin panel."""
        user = UserRepository.get_by_id_any(user_id)
        if not user:
            return AdminActionResult(False, 'Không tìm thấy người dùng.')

        username = username.strip()
        full_name = full_name.strip()

        if len(username) < 3:
            return AdminActionResult(False, 'Tên đăng nhập phải có ít nhất 3 ký tự.')
        if not validate_username_format(username):
            return AdminActionResult(False, 'Tên đăng nhập không hợp lệ.')
        if UserRepository.username_exists(username, exclude_id=user.id):
            return AdminActionResult(False, 'Tên đăng nhập đã tồn tại.')
        if role not in {UserRole.ADMIN.value, UserRole.USER.value}:
            return AdminActionResult(False, 'Vai trò không hợp lệ.')

        if actor and actor.id == user.id and not is_active:
            return AdminActionResult(False, 'Không thể vô hiệu hóa chính tài khoản admin đang đăng nhập.')
        if actor and actor.id == user.id and role != UserRole.ADMIN.value:
            return AdminActionResult(False, 'Không thể hạ quyền chính tài khoản đang đăng nhập.')

        user.username = username
        user.full_name = full_name or None
        user.role = role
        user.is_active = is_active

        if new_password:
            if len(new_password) < 6:
                return AdminActionResult(False, 'Mật khẩu mới phải có ít nhất 6 ký tự.')
            user.password = PasswordService.hash_password(new_password)

        UserRepository.save(user)
        return AdminActionResult(True, 'Cập nhật người dùng thành công.')

    @staticmethod
    def deactivate_user(user_id: int, actor: User) -> AdminActionResult:
        """Khóa tài khoản — is_active=False."""
        if actor.id == user_id:
            return AdminActionResult(False, 'Không thể vô hiệu hóa chính mình.')
        user = UserRepository.get_by_id_any(user_id)
        if not user:
            return AdminActionResult(False, 'Không tìm thấy người dùng.')
        if not user.is_active:
            return AdminActionResult(False, 'Tài khoản đã bị khóa.')
        user.is_active = False
        UserRepository.save(user)
        return AdminActionResult(True, 'Đã khóa người dùng.')

    @staticmethod
    def activate_user(user_id: int) -> AdminActionResult:
        """Mở khóa tài khoản — is_active=True."""
        user = UserRepository.get_by_id_any(user_id)
        if not user:
            return AdminActionResult(False, 'Không tìm thấy người dùng.')
        if user.is_active:
            return AdminActionResult(False, 'Tài khoản đang hoạt động.')
        user.is_active = True
        UserRepository.save(user)
        return AdminActionResult(True, 'Đã mở khóa người dùng.')

    @staticmethod
    def delete_user(user_id: int, actor: User) -> AdminActionResult:
        """Xóa vĩnh viễn user và dữ liệu liên quan (CASCADE)."""
        if actor.id == user_id:
            return AdminActionResult(False, 'Không thể xóa chính tài khoản đang đăng nhập.')

        user = UserRepository.get_by_id_any(user_id)
        if not user:
            return AdminActionResult(False, 'Không tìm thấy người dùng.')

        if user.role == UserRole.ADMIN.value:
            admin_count = User.objects.filter(role=UserRole.ADMIN.value, is_active=True).count()
            if admin_count <= 1 and user.is_active:
                return AdminActionResult(False, 'Không thể xóa quản trị viên cuối cùng.')

        UserRepository.delete_user(user)
        return AdminActionResult(True, 'Đã xóa người dùng và dữ liệu liên quan.')
