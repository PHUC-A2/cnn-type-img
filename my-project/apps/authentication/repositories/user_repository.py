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
    def username_exists(username: str) -> bool:
        return User.objects.filter(username=username).exists()

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
