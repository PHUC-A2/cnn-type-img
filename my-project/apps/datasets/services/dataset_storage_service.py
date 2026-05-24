"""Lưu trữ file dataset trên media/datasets/."""

import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify

from apps.datasets.repositories.dataset_repository import DatasetRepository


class DatasetStorageService:
    """Service lưu/xóa thư mục dataset trên file system."""

    DATASET_DIR = 'datasets'

    @classmethod
    def generate_unique_slug(cls, name: str) -> str:
        """Tạo slug duy nhất từ tên dataset."""
        base = slugify(name) or 'dataset'
        slug = base
        if not DatasetRepository.slug_exists(slug):
            return slug
        return f'{base}-{uuid.uuid4().hex[:8]}'

    @classmethod
    def get_dataset_dir(cls, slug: str) -> Path:
        """Đường dẫn thư mục dataset trên disk."""
        return Path(settings.MEDIA_ROOT) / cls.DATASET_DIR / slug

    @classmethod
    def get_relative_path(cls, slug: str) -> str:
        """Path lưu DB — relative trong media."""
        return f'{cls.DATASET_DIR}/{slug}/'

    @classmethod
    def build_image_url(cls, slug: str, class_slug: str, filename: str) -> str:
        """URL public của ảnh dataset."""
        return f'{settings.MEDIA_URL}{cls.DATASET_DIR}/{slug}/{class_slug}/{filename}'

    @classmethod
    def ensure_dataset_dir(cls, slug: str) -> Path:
        """Tạo thư mục dataset nếu chưa có."""
        path = cls.get_dataset_dir(slug)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def remove_dataset_dir(cls, slug: str) -> None:
        """Xóa toàn bộ thư mục dataset."""
        path = cls.get_dataset_dir(slug)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    @classmethod
    def copy_class_images(cls, slug: str, class_slug: str, source_dir: Path) -> Path:
        """Copy ảnh class vào thư mục dataset permanent."""
        dest = cls.get_dataset_dir(slug) / class_slug
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source_dir, dest)
        return dest
