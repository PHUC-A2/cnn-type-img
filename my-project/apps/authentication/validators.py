"""Validator dùng chung cho form authentication."""

import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_AVATAR_SIZE_MB = 5


def validate_email_format(email: str) -> bool:
    """Kiểm tra định dạng email — không dùng HTML5 type=email."""
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_username_format(username: str) -> bool:
    """Tên đăng nhập chỉ gồm chữ, số và dấu gạch dưới."""
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username.strip()))
