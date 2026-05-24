"""Repository training jobs."""

from typing import Optional

from apps.authentication.models import User
from apps.training.models import TrainingHistory, TrainingJob


class TrainingJobRepository:
    """Truy vấn bảng training_jobs."""

    @staticmethod
    def get_by_id(job_id: int) -> Optional[TrainingJob]:
        try:
            return TrainingJob.objects.select_related(
                'model', 'dataset', 'trained_by'
            ).get(id=job_id)
        except TrainingJob.DoesNotExist:
            return None

    @staticmethod
    def create(**kwargs) -> TrainingJob:
        return TrainingJob.objects.create(**kwargs)

    @staticmethod
    def save(job: TrainingJob) -> TrainingJob:
        job.save()
        return job

    @staticmethod
    def list_for_user(user: User):
        qs = TrainingJob.objects.select_related('model', 'dataset').order_by('-created_at')
        if not user.is_admin:
            qs = qs.filter(trained_by_id=user.id)
        return qs

    @staticmethod
    def user_can_access(user: User, job: TrainingJob) -> bool:
        return user.is_admin or job.trained_by_id == user.id


class TrainingHistoryRepository:
    """Truy vấn training_history."""

    @staticmethod
    def create(**kwargs) -> TrainingHistory:
        return TrainingHistory.objects.create(**kwargs)

    @staticmethod
    def list_by_job(job_id: int):
        return TrainingHistory.objects.filter(training_job_id=job_id).order_by('epoch_number')
