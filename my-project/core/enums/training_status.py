"""Trạng thái job huấn luyện CNN."""

from enum import Enum


class TrainingStatus(str, Enum):
    """Các trạng thái training job."""

    PENDING = 'pending'
    PREPARING = 'preparing'
    TRAINING = 'training'
    VALIDATING = 'validating'
    COMPLETED = 'completed'
    FAILED = 'failed'

    @classmethod
    def choices(cls):
        return [(item.value, item.label_vi()) for item in cls]

    def label_vi(self) -> str:
        labels = {
            TrainingStatus.PENDING: 'Chờ xử lý',
            TrainingStatus.PREPARING: 'Đang chuẩn bị',
            TrainingStatus.TRAINING: 'Đang huấn luyện',
            TrainingStatus.VALIDATING: 'Đang kiểm tra',
            TrainingStatus.COMPLETED: 'Hoàn thành',
            TrainingStatus.FAILED: 'Thất bại',
        }
        return labels[self]
