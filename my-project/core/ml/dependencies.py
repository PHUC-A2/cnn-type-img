"""Kiểm tra thư viện ML — lazy import tránh crash khi thiếu package."""

from typing import Tuple


def check_tensorflow() -> Tuple[bool, str]:
    """TensorFlow/Keras có sẵn để huấn luyện thật."""
    try:
        import tensorflow  # noqa: F401
        return True, ''
    except ImportError:
        return False, 'Chưa cài TensorFlow. Chạy: pip install tensorflow'


def check_numpy() -> bool:
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


def check_sklearn() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False
