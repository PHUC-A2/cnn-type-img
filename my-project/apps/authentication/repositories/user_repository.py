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
    def email_exists(email: str) -> bool:
        return User.objects.filter(email=email).exists()

    @staticmethod
    def create_user(**kwargs) -> User:
        return User.objects.create(**kwargs)

    @staticmethod
    def save(user: User) -> User:
        user.save()
        return user
