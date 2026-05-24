"""Lưu file model .h5 vào trained_models/."""

import uuid
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify

from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository


class ModelStorageService:
    """Quản lý thư mục trained_models/."""

    @classmethod
    def generate_unique_slug(cls, name: str) -> str:
        base = slugify(name) or 'model'
        slug = base
        if not CnnModelRepository.slug_exists(slug):
            return slug
        return f'{base}-{uuid.uuid4().hex[:8]}'

    @classmethod
    def get_model_dir(cls, slug: str) -> Path:
        path = Path(settings.MODEL_ROOT) / slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def build_model_path(cls, slug: str, job_id: int) -> Path:
        """Đường dẫn file .h5 trên disk."""
        return cls.get_model_dir(slug) / f'job_{job_id}.h5'

    @classmethod
    def relative_model_path(cls, slug: str, job_id: int) -> str:
        """Path lưu DB — relative trong MODEL_ROOT."""
        return f'{slug}/job_{job_id}.h5'

    @classmethod
    def get_file_size_mb(cls, file_path: Path) -> float:
        if not file_path.exists():
            return 0.0
        return round(file_path.stat().st_size / (1024 * 1024), 3)
