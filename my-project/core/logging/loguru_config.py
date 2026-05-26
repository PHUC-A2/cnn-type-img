"""Cấu hình loguru — ghi file + stderr."""

import sys
from pathlib import Path

from django.conf import settings


def setup_loguru() -> None:
    """Khởi tạo loguru khi Django ready — tránh gọi nhiều lần."""
    try:
        from loguru import logger
    except ImportError:
        return

    if getattr(setup_loguru, '_configured', False):
        return

    logger.remove()
    logger.add(sys.stderr, level='INFO', colorize=True)

    logs_dir = Path(settings.BASE_DIR) / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(logs_dir / 'app_{time:YYYY-MM-DD}.log'),
        rotation='00:00',
        retention='14 days',
        level='DEBUG',
        encoding='utf-8',
    )

    setup_loguru._configured = True
