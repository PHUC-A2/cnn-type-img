"""Service mã hóa và kiểm tra mật khẩu."""

from django.contrib.auth.hashers import check_password, make_password


class PasswordService:
    """Xử lý hash/verify mật khẩu — không dùng django.contrib.auth User."""

    @staticmethod
    def hash_password(raw_password: str) -> str:
        return make_password(raw_password)

    @staticmethod
    def verify_password(raw_password: str, hashed_password: str) -> bool:
        return check_password(raw_password, hashed_password)
