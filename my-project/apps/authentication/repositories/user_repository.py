"""User repository — truy vấn DB tách khỏi service."""

from typing import Optional

from apps.authentication.models import User


class UserRepository:
    """Repository thao tác bảng users."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_by_id_any(user_id: int) -> Optional[User]:
        """Lấy user kể cả đã vô hiệu hóa — dùng cho admin panel."""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def list_all(include_inactive: bool = True):
        """Danh sách toàn bộ user — chỉ admin."""
        qs = User.objects.all().order_by('-created_at')
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        try:
            return User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        try:
            return User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            return None

    @staticmethod
    def username_exists(username: str, exclude_id: int | None = None) -> bool:
        """Kiểm tra trùng username — có thể loại trừ user hiện tại."""
        qs = User.objects.filter(username=username)
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    @staticmethod
    def email_exists(email: str, exclude_id: int | None = None) -> bool:
        qs = User.objects.filter(email=email)
        if exclude_id is not None:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    @staticmethod
    def create_user(**kwargs) -> User:
        return User.objects.create(**kwargs)

    @staticmethod
    def save(user: User) -> User:
        user.save()
        return user

    @staticmethod
    def delete_user(user: User) -> None:
        """Xóa vĩnh viễn user — cascade dữ liệu liên quan."""
        user.delete()
