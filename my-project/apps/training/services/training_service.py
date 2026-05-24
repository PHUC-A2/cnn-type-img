"""Orchestrator huấn luyện — tạo job, chạy background thread."""

import threading
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from apps.authentication.models import User
from apps.datasets.models import Dataset
from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.models_ai.models import CnnModel
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.training.models import TrainingJob
from apps.training.repositories.training_job_repository import TrainingJobRepository
from apps.training.services.model_storage_service import ModelStorageService
from core.enums.training_status import TrainingStatus
from core.ml.dependencies import check_tensorflow


@dataclass
class TrainingStartResult:
    """Kết quả khởi tạo job huấn luyện."""

    success: bool
    message: str
    job: Optional[TrainingJob] = None


class TrainingService:
    """Service nghiệp vụ huấn luyện CNN."""

    @staticmethod
    def start_training(
        user: User,
        dataset_id: int,
        model_name: str,
        description: str,
        input_width: int,
        input_height: int,
        epochs: int,
        batch_size: int,
        learning_rate: float,
        optimizer: str,
        loss_function: str,
    ) -> TrainingStartResult:
        dataset = DatasetRepository.get_by_id(dataset_id)
        if not dataset:
            return TrainingStartResult(False, 'Không tìm thấy bộ dữ liệu.')
        if not DatasetRepository.user_can_access(user, dataset):
            return TrainingStartResult(False, 'Bạn không có quyền dùng bộ dữ liệu này.')
        if dataset.total_images < 4:
            return TrainingStartResult(False, 'Bộ dữ liệu cần ít nhất 4 ảnh để huấn luyện.')

        tf_ok, tf_msg = check_tensorflow()
        if not tf_ok and not settings.TRAINING_SIMULATION_MODE:
            return TrainingStartResult(False, tf_msg)

        model_name = model_name.strip()
        slug = ModelStorageService.generate_unique_slug(model_name)

        cnn_model = CnnModelRepository.create(
            model_name=model_name,
            model_slug=slug,
            description=description or None,
            architecture_type='cnn_basic',
            framework='tensorflow',
            input_width=input_width,
            input_height=input_height,
            channels=3,
            version='1.0.0',
            created_by=user,
            is_active=True,
        )

        job = TrainingJobRepository.create(
            model=cnn_model,
            dataset=dataset,
            trained_by=user,
            training_status=TrainingStatus.PENDING.value,
            status_message='Đang chờ bắt đầu huấn luyện...',
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            optimizer=optimizer,
            loss_function=loss_function,
        )

        TrainingService.launch_background(job.id, use_simulation=not tf_ok)
        mode = 'mô phỏng' if not tf_ok else 'thật'
        return TrainingStartResult(
            success=True,
            message=f'Đã bắt đầu huấn luyện ({mode}).',
            job=job,
        )

    @staticmethod
    def launch_background(job_id: int, use_simulation: bool = False) -> None:
        """Chạy trainer trong thread — không block HTTP request."""
        if use_simulation:
            from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
            target = SimulationTrainerService.run
        else:
            from apps.training.services.cnn.trainer import CnnTrainerService
            target = CnnTrainerService.run

        thread = threading.Thread(target=target, args=(job_id,), daemon=True)
        thread.start()

    @staticmethod
    def get_progress_percent(job: TrainingJob) -> int:
        if job.training_status == TrainingStatus.COMPLETED.value:
            return 100
        if job.training_status == TrainingStatus.FAILED.value:
            return 100
        if job.epochs <= 0:
            return 0
        done = job.history.count()
        return min(99, int(done / job.epochs * 100))
