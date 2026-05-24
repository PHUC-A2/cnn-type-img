"""Lưu avatar người dùng lên media/avatars/."""

from typing import Optional

import os
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile


class AvatarStorageService:
    """Service lưu file avatar — DB chỉ lưu path."""

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    MAX_SIZE_MB = 5

    @classmethod
    def save_avatar(cls, uploaded_file: UploadedFile, user_id: int) -> str:
        ext = Path(uploaded_file.name).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError('Chỉ chấp nhận ảnh JPG, PNG, WEBP, GIF.')

        if uploaded_file.size > cls.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f'Ảnh không được vượt quá {cls.MAX_SIZE_MB}MB.')

        avatar_dir = Path(settings.MEDIA_ROOT) / 'avatars'
        avatar_dir.mkdir(parents=True, exist_ok=True)

        filename = f'user_{user_id}_{uuid.uuid4().hex}{ext}'
        file_path = avatar_dir / filename

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return f'{settings.MEDIA_URL}avatars/{filename}'

    @classmethod
    def delete_old_avatar(cls, avatar_url: Optional[str]) -> None:
        if not avatar_url or not avatar_url.startswith(settings.MEDIA_URL):
            return
        relative = avatar_url.replace(settings.MEDIA_URL, '', 1)
        file_path = Path(settings.MEDIA_ROOT) / relative
        if file_path.exists():
            os.remove(file_path)
