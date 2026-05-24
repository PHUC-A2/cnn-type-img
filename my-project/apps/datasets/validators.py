"""Hằng số và helper validate dataset/ảnh."""

from pathlib import Path

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
ALLOWED_ZIP_EXTENSIONS = {'.zip'}

MIME_BY_EXT = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
}

MIN_CLASSES = 2
MIN_IMAGES_PER_CLASS = 1


def is_image_file(path: Path) -> bool:
    """Kiểm tra file có phải ảnh được hỗ trợ."""
    return path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def is_zip_file(filename: str) -> bool:
    """Kiểm tra file upload có phải ZIP."""
    return Path(filename).suffix.lower() in ALLOWED_ZIP_EXTENSIONS
