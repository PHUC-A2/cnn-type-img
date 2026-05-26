"""Mức độ log hệ thống."""

from enum import Enum


class LogLevel(str, Enum):
    """Level log — map bảng system_logs."""

    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

    @classmethod
    def choices(cls):
        return [(item.value, item.label_vi()) for item in cls]

    def label_vi(self) -> str:
        labels = {
            LogLevel.INFO: 'Thông tin',
            LogLevel.WARNING: 'Cảnh báo',
            LogLevel.ERROR: 'Lỗi',
        }
        return labels[self]
