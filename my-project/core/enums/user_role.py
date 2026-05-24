from enum import Enum


class UserRole(str, Enum):
    """Vai trò người dùng trong hệ thống."""

    ADMIN = 'admin'
    USER = 'user'

    @classmethod
    def choices(cls):
        # Trả về tuple cho Django model choices
        return [(item.value, item.label_vi()) for item in cls]

    def label_vi(self) -> str:
        labels = {
            UserRole.ADMIN: 'Quản trị viên',
            UserRole.USER: 'Người dùng',
        }
        return labels[self]
