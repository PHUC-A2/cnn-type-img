"""Chuẩn bị thư mục train/val từ dataset images."""

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings

from apps.datasets.models import Dataset
from apps.datasets.repositories.dataset_image_repository import DatasetImageRepository


@dataclass
class PreprocessResult:
    """Kết quả chuẩn bị thư mục huấn luyện."""

    root: Path
    copied: int = 0
    skipped: list = field(default_factory=list)


class DatasetPreprocessorService:
    """Tạo cấu trúc thư mục cho Keras flow_from_directory."""

    MIN_VALID_IMAGES = 4

    @classmethod
    def prepare_training_dirs(cls, dataset: Dataset, job_id: int) -> Path:
        """
        Tạo temp dir:
        root/train/class_name/*.jpg
        root/val/class_name/*.jpg
        Chỉ copy ảnh đọc được bằng Pillow — bỏ qua file lỗi/0 byte.
        """
        result = cls.build_training_dirs(dataset, job_id)
        return result.root

    @classmethod
    def build_training_dirs(cls, dataset: Dataset, job_id: int) -> PreprocessResult:
        root = Path(tempfile.mkdtemp(prefix=f'train_job_{job_id}_'))
        train_root = root / 'train'
        val_root = root / 'val'
        train_root.mkdir(parents=True)
        val_root.mkdir(parents=True)

        images = DatasetImageRepository.list_paths_for_training(dataset.id)
        if not images:
            cls.cleanup(root)
            raise ValueError('Bộ dữ liệu không có ảnh để huấn luyện.')

        copied = 0
        skipped: list[str] = []

        for item in images:
            src = cls._resolve_image_path(item['image_url'])
            if not cls._is_valid_image(src):
                skipped.append(item['image_name'])
                continue

            split_dir = train_root if item['is_train'] else val_root
            class_dir = split_dir / item['class_name']
            class_dir.mkdir(parents=True, exist_ok=True)
            dest = class_dir / item['image_name']
            if not dest.exists():
                shutil.copy2(src, dest)
            copied += 1

        if copied < cls.MIN_VALID_IMAGES:
            cls.cleanup(root)
            preview = ', '.join(skipped[:5])
            suffix = '...' if len(skipped) > 5 else ''
            raise ValueError(
                f'Không đủ ảnh hợp lệ để huấn luyện (còn {copied} ảnh). '
                f'Đã bỏ qua {len(skipped)} ảnh lỗi: {preview}{suffix}.'
            )

        try:
            cls._ensure_not_empty(train_root, 'huấn luyện')
            cls._ensure_not_empty(val_root, 'kiểm tra')
        except ValueError:
            cls.cleanup(root)
            preview = ', '.join(skipped[:5])
            suffix = '...' if len(skipped) > 5 else ''
            raise ValueError(
                f'Tập train/val không hợp lệ sau khi lọc ảnh lỗi. '
                f'Đã bỏ qua {len(skipped)} ảnh: {preview}{suffix}.'
            ) from None

        return PreprocessResult(root=root, copied=copied, skipped=skipped)

    @staticmethod
    def _is_valid_image(src: Path) -> bool:
        """Kiểm tra ảnh tồn tại, có dung lượng và Pillow đọc được."""
        if not src.exists() or src.stat().st_size == 0:
            return False
        try:
            from PIL import Image
            with Image.open(src) as img:
                img.verify()
            with Image.open(src) as img:
                img.load()
            return True
        except Exception:
            return False

    @staticmethod
    def _resolve_image_path(image_url: str) -> Path:
        """Chuyển URL media thành path trên disk."""
        relative = image_url.replace(settings.MEDIA_URL, '', 1).lstrip('/')
        return Path(settings.MEDIA_ROOT) / relative

    @staticmethod
    def _ensure_not_empty(folder: Path, label: str) -> None:
        has_files = any(f.is_file() for f in folder.rglob('*'))
        if not has_files:
            raise ValueError(f'Không có ảnh tập {label}.')

    @classmethod
    def cleanup(cls, root: Path) -> None:
        if root and root.exists():
            shutil.rmtree(root, ignore_errors=True)
