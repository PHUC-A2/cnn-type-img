"""Validate cấu trúc dataset và ảnh — Pillow detect corrupt (fallback nếu thiếu Pillow)."""

import imghdr
import struct
from dataclasses import dataclass
from pathlib import Path

from apps.datasets.validators import (
    ALLOWED_IMAGE_EXTENSIONS,
    MIN_CLASSES,
    MIN_IMAGES_PER_CLASS,
    MIME_BY_EXT,
    is_image_file,
)

try:
    from PIL import Image, UnidentifiedImageError
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


@dataclass
class ImageMeta:
    """Metadata ảnh sau khi validate."""

    width: int
    height: int
    channels: int
    image_format: str
    mime_type: str
    file_size: int


@dataclass
class ClassFolder:
    """Thư mục class và danh sách ảnh hợp lệ."""

    class_name: str
    folder_path: Path
    image_paths: list


class DatasetValidationService:
    """Validate ZIP structure, class folders và từng ảnh."""

    @staticmethod
    def find_dataset_root(base_path: Path) -> Path:
        """Tìm thư mục gốc chứa các folder class (cat/, dog/, ...)."""
        base_path = Path(base_path)

        def has_class_structure(path: Path) -> bool:
            subdirs = [
                d for d in path.iterdir()
                if d.is_dir() and not d.name.startswith('.') and d.name != '__MACOSX'
            ]
            if not subdirs:
                return False
            for subdir in subdirs:
                if any(is_image_file(f) for f in subdir.iterdir() if f.is_file()):
                    return True
            return False

        if has_class_structure(base_path):
            return base_path

        subdirs = [
            d for d in base_path.iterdir()
            if d.is_dir() and not d.name.startswith('.') and d.name != '__MACOSX'
        ]
        files = [f for f in base_path.iterdir() if f.is_file()]
        if len(subdirs) == 1 and not files:
            candidate = subdirs[0]
            if has_class_structure(candidate):
                return candidate

        raise ValueError(
            'Cấu trúc bộ dữ liệu không hợp lệ. '
            'ZIP cần chứa các thư mục class, mỗi class có ít nhất một ảnh.'
        )

    @staticmethod
    def scan_class_folders(root_path: Path) -> list:
        """Quét các thư mục class và ảnh bên trong."""
        classes = []
        for class_dir in sorted(root_path.iterdir()):
            if not class_dir.is_dir() or class_dir.name.startswith('.') or class_dir.name == '__MACOSX':
                continue

            image_paths = sorted(
                f for f in class_dir.iterdir()
                if f.is_file() and is_image_file(f)
            )
            if not image_paths:
                raise ValueError(f'Class "{class_dir.name}" không có ảnh hợp lệ.')

            classes.append(ClassFolder(
                class_name=class_dir.name,
                folder_path=class_dir,
                image_paths=image_paths,
            ))

        if len(classes) < MIN_CLASSES:
            raise ValueError(f'Bộ dữ liệu cần ít nhất {MIN_CLASSES} class để phân loại.')

        for cls in classes:
            if len(cls.image_paths) < MIN_IMAGES_PER_CLASS:
                raise ValueError(
                    f'Class "{cls.class_name}" cần ít nhất {MIN_IMAGES_PER_CLASS} ảnh.'
                )

        return classes

    @staticmethod
    def validate_image_file(file_path: Path) -> ImageMeta:
        """Validate ảnh — ưu tiên Pillow, fallback imghdr."""
        if HAS_PILLOW:
            return DatasetValidationService._validate_with_pillow(file_path)
        return DatasetValidationService._validate_without_pillow(file_path)

    @staticmethod
    def _validate_with_pillow(file_path: Path) -> ImageMeta:
        ext = file_path.suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f'Định dạng {ext} không được hỗ trợ.')

        try:
            with Image.open(file_path) as img:
                img.verify()

            with Image.open(file_path) as img:
                img.load()
                width, height = img.size
                channels = len(img.getbands())
                image_format = (img.format or ext.lstrip('.')).lower()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError(f'Ảnh lỗi hoặc corrupt: {file_path.name}') from exc

        return ImageMeta(
            width=width,
            height=height,
            channels=channels,
            image_format=image_format,
            mime_type=MIME_BY_EXT.get(ext, 'application/octet-stream'),
            file_size=file_path.stat().st_size,
        )

    @staticmethod
    def _validate_without_pillow(file_path: Path) -> ImageMeta:
        """Fallback khi môi trường chưa cài Pillow (dev mingw)."""
        ext = file_path.suffix.lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(f'Định dạng {ext} không được hỗ trợ.')

        with open(file_path, 'rb') as handle:
            header = handle.read(512)

        kind = imghdr.what(None, header)
        if not kind and ext in {'.jpg', '.jpeg'}:
            kind = 'jpeg'
        if not kind:
            raise ValueError(f'Ảnh lỗi hoặc corrupt: {file_path.name}')

        width, height, channels = DatasetValidationService._read_basic_dimensions(
            file_path, kind, header
        )

        return ImageMeta(
            width=width,
            height=height,
            channels=channels,
            image_format=kind,
            mime_type=MIME_BY_EXT.get(ext, 'application/octet-stream'),
            file_size=file_path.stat().st_size,
        )

    @staticmethod
    def _read_basic_dimensions(file_path: Path, kind: str, header: bytes) -> tuple:
        """Đọc kích thước cơ bản không cần Pillow."""
        if kind == 'png' and len(header) >= 24:
            width, height = struct.unpack('>II', header[16:24])
            return width, height, 4

        if kind in ('jpeg', 'jpg'):
            with open(file_path, 'rb') as handle:
                handle.seek(2)
                while True:
                    marker = handle.read(2)
                    if len(marker) < 2:
                        break
                    if marker[0] != 0xFF:
                        break
                    if marker[1] in (0xC0, 0xC1, 0xC2):
                        handle.read(3)
                        data = handle.read(4)
                        if len(data) == 4:
                            height, width = struct.unpack('>HH', data)
                            return width, height, 3
                    else:
                        length_bytes = handle.read(2)
                        if len(length_bytes) < 2:
                            break
                        length = struct.unpack('>H', length_bytes)[0]
                        handle.seek(length - 2, 1)

        return 0, 0, 3
