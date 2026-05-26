"""Quản lý phiên bản model — tạo version khi train xong, đặt production."""

from dataclasses import dataclass
from typing import Optional

from apps.models_ai.models import CnnModel, ModelVersion
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.training.models import TrainingJob
from apps.training.repositories.training_job_repository import TrainingJobRepository
from core.enums.training_status import TrainingStatus


@dataclass
class VersionActionResult:
    """Kết quả thao tác trên phiên bản model."""

    success: bool
    message: str
    version: Optional[ModelVersion] = None


class ModelVersionService:
    """Service versioning — hook sau huấn luyện và quản lý production."""

    @staticmethod
    def on_training_completed(job_id: int) -> Optional[ModelVersion]:
        """Tạo phiên bản mới sau khi job huấn luyện xong (trước hoặc sau cập nhật COMPLETED)."""
        job = TrainingJobRepository.get_by_id(job_id)
        if not job or job.training_status == TrainingStatus.FAILED.value:
            return None
        if not job.model.model_file_path:
            return None
        return ModelVersionService.create_from_completed_job(job)

    @staticmethod
    def create_from_completed_job(job: TrainingJob) -> Optional[ModelVersion]:
        """Ghi nhận file .h5 thành một bản ghi model_versions."""
        cnn = job.model
        if not cnn.model_file_path:
            return None
        if ModelVersionRepository.path_exists(cnn.id, cnn.model_file_path):
            return ModelVersionRepository.get_production(cnn.id)

        metrics = job.metrics.first()
        accuracy = job.validation_accuracy
        if accuracy is None and metrics:
            accuracy = metrics.accuracy

        version_number = ModelVersionService._next_version_number(cnn.id)
        is_production = not ModelVersionRepository.has_production(cnn.id)

        version = ModelVersionRepository.create(
            model=cnn,
            version_name=f'Huấn luyện job #{job.id}',
            version_number=version_number,
            model_path=cnn.model_file_path,
            accuracy_score=accuracy,
            is_production=is_production,
        )

        if is_production:
            cnn.version = version_number
            CnnModelRepository.save(cnn)

        return version

    @staticmethod
    def sync_missing_versions() -> int:
        """Backfill phiên bản cho model cũ đã có file nhưng chưa có bản ghi version."""
        synced = 0
        models = CnnModel.objects.filter(is_active=True).exclude(model_file_path__isnull=True).exclude(model_file_path='')
        for cnn in models:
            if ModelVersionRepository.count_by_model(cnn.id) > 0:
                continue
            job = (
                TrainingJob.objects.filter(
                    model_id=cnn.id,
                    training_status=TrainingStatus.COMPLETED.value,
                )
                .order_by('-finished_at', '-id')
                .first()
            )
            if job and ModelVersionService.create_from_completed_job(job):
                synced += 1
        return synced

    @staticmethod
    def set_production(model_id: int, version_id: int) -> VersionActionResult:
        """Đặt một phiên bản làm production — bỏ cờ các bản khác."""
        version = ModelVersionRepository.get_by_id(version_id)
        if not version or version.model_id != model_id:
            return VersionActionResult(False, 'Không tìm thấy phiên bản mô hình.')

        ModelVersionRepository.clear_production_flags(model_id)
        version.is_production = True
        ModelVersionRepository.save(version)

        cnn = version.model
        cnn.version = version.version_number
        cnn.model_file_path = version.model_path
        CnnModelRepository.save(cnn)

        return VersionActionResult(True, f'Đã đặt phiên bản {version.version_number} làm production.', version)

    @staticmethod
    def _next_version_number(model_id: int) -> str:
        """Sinh số phiên bản tiếp theo — 1.0.1, 1.0.2..."""
        count = ModelVersionRepository.count_by_model(model_id)
        return f'1.0.{count + 1}'
