"""Thống kê tổng quan admin panel — query cross-table."""

from dataclasses import dataclass

from django.db.models import Avg

from apps.authentication.models import User
from apps.datasets.models import Dataset
from apps.models_ai.models import CnnModel
from apps.predictions.models import Prediction
from apps.training.models import TrainingJob
from core.enums.training_status import TrainingStatus


@dataclass
class AdminDashboardStats:
    """Số liệu tổng quan hệ thống."""

    total_users: int
    active_users: int
    total_datasets: int
    total_models: int
    total_training_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_predictions: int
    avg_confidence: float | None
    recent_users: list
    recent_jobs: list


class AdminDashboardService:
    """Aggregate queries cho /admin-panel/."""

    @staticmethod
    def build_stats() -> AdminDashboardStats:
        completed = TrainingStatus.COMPLETED.value
        failed = TrainingStatus.FAILED.value
        avg_conf = Prediction.objects.aggregate(v=Avg('confidence_score'))['v']

        return AdminDashboardStats(
            total_users=User.objects.count(),
            active_users=User.objects.filter(is_active=True).count(),
            total_datasets=Dataset.objects.filter(is_active=True).count(),
            total_models=CnnModel.objects.filter(is_active=True).count(),
            total_training_jobs=TrainingJob.objects.count(),
            completed_jobs=TrainingJob.objects.filter(training_status=completed).count(),
            failed_jobs=TrainingJob.objects.filter(training_status=failed).count(),
            total_predictions=Prediction.objects.count(),
            avg_confidence=round(float(avg_conf), 4) if avg_conf is not None else None,
            recent_users=list(User.objects.order_by('-created_at')[:5]),
            recent_jobs=list(
                TrainingJob.objects.select_related('model', 'trained_by')
                .order_by('-created_at')[:5]
            ),
        )
