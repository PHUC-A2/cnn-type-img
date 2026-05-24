"""Huấn luyện mô phỏng — dùng khi môi trường dev chưa có TensorFlow."""

import random
import time

from django.utils import timezone

from apps.training.models import ModelMetrics, TrainingHistory
from apps.training.repositories.training_job_repository import TrainingJobRepository
from apps.training.services.model_storage_service import ModelStorageService
from core.enums.training_status import TrainingStatus


class SimulationTrainerService:
    """Mô phỏng epoch metrics + file placeholder cho UI dev/test."""

    @classmethod
    def run(cls, job_id: int) -> None:
        from django.db import close_old_connections
        close_old_connections()

        job = TrainingJobRepository.get_by_id(job_id)
        if not job:
            return

        started = time.time()
        try:
            cls._set_status(job, TrainingStatus.PREPARING, 'Đang chuẩn bị dữ liệu (mô phỏng)...')
            time.sleep(0.5)

            cls._set_status(job, TrainingStatus.TRAINING, 'Đang huấn luyện mô hình (mô phỏng)...')
            train_loss = 1.2
            val_loss = 1.3
            train_acc = 0.45
            val_acc = 0.42

            for epoch in range(1, job.epochs + 1):
                time.sleep(0.4)
                train_loss = max(0.08, train_loss * random.uniform(0.75, 0.9))
                val_loss = max(0.1, val_loss * random.uniform(0.78, 0.92))
                train_acc = min(0.99, train_acc + random.uniform(0.03, 0.08))
                val_acc = min(0.97, val_acc + random.uniform(0.02, 0.07))

                TrainingHistory.objects.create(
                    training_job=job,
                    epoch_number=epoch,
                    train_accuracy=round(train_acc, 4),
                    validation_accuracy=round(val_acc, 4),
                    train_loss=round(train_loss, 4),
                    validation_loss=round(val_loss, 4),
                )
                job.train_accuracy = round(train_acc, 4)
                job.validation_accuracy = round(val_acc, 4)
                job.train_loss = round(train_loss, 4)
                job.validation_loss = round(val_loss, 4)
                job.status_message = f'Epoch {epoch}/{job.epochs} — đang huấn luyện (mô phỏng)...'
                TrainingJobRepository.save(job)

            cls._set_status(job, TrainingStatus.VALIDATING, 'Đang tính metrics (mô phỏng)...')
            model_path = ModelStorageService.build_model_path(job.model.model_slug, job.id)
            model_path.write_text('SIMULATED_MODEL_PLACEHOLDER', encoding='utf-8')

            cnn = job.model
            cnn.total_parameters = 125000
            cnn.model_file_path = ModelStorageService.relative_model_path(cnn.model_slug, job.id)
            cnn.model_size_mb = ModelStorageService.get_file_size_mb(model_path)
            cnn.save()

            ModelMetrics.objects.create(
                training_job=job,
                accuracy=job.validation_accuracy,
                precision_score=job.validation_accuracy,
                recall_score=job.validation_accuracy,
                f1_score=job.validation_accuracy,
            )

            job.execution_time = round(time.time() - started, 2)
            job.finished_at = timezone.now()
            cls._set_status(job, TrainingStatus.COMPLETED, 'Huấn luyện hoàn thành (chế độ mô phỏng).')
        except Exception as exc:
            job.execution_time = round(time.time() - started, 2)
            job.finished_at = timezone.now()
            cls._set_status(job, TrainingStatus.FAILED, f'Huấn luyện thất bại: {exc}')
        finally:
            close_old_connections()

    @staticmethod
    def _set_status(job, status: TrainingStatus, message: str) -> None:
        job.training_status = status.value
        job.status_message = message
        if status == TrainingStatus.TRAINING and not job.started_at:
            job.started_at = timezone.now()
        TrainingJobRepository.save(job)
