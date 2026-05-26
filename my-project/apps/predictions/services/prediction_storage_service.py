"""Lưu ảnh predict vào media/predictions/."""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile


class PredictionStorageService:
    """Service lưu ảnh upload phân loại — DB chỉ lưu URL."""

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    MAX_SIZE_MB = 10

    @classmethod
    def save_image(cls, uploaded_file: UploadedFile, user_id: int) -> tuple[str, str]:
        """Lưu file và trả về (image_name, image_url)."""
        ext = Path(uploaded_file.name).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise ValueError('Chỉ chấp nhận ảnh JPG, PNG, WEBP, GIF, BMP.')

        if uploaded_file.size > cls.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f'Ảnh không được vượt quá {cls.MAX_SIZE_MB}MB.')

        predict_dir = Path(settings.MEDIA_ROOT) / 'predictions'
        predict_dir.mkdir(parents=True, exist_ok=True)

        filename = f'user_{user_id}_{uuid.uuid4().hex}{ext}'
        file_path = predict_dir / filename

        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        return filename, f'{settings.MEDIA_URL}predictions/{filename}'

    @classmethod
    def resolve_path(cls, image_url: str) -> Path:
        """Chuyển URL media thành path tuyệt đối."""
        relative = image_url.replace(settings.MEDIA_URL, '', 1)
        return Path(settings.MEDIA_ROOT) / relative
