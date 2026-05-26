"""Tổng hợp dữ liệu hiển thị danh sách/chi tiết mô hình."""

from dataclasses import dataclass
from typing import Optional

from apps.authentication.models import User
from apps.models_ai.models import CnnModel, ModelVersion
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.models_ai.services.model_loader_service import ModelLoaderService
from apps.models_ai.services.model_version_service import ModelVersionService
from core.enums.training_status import TrainingStatus


@dataclass
class ModelCardView:
    """DTO card mô hình trên trang danh sách."""

    model: CnnModel
    production_version: Optional[ModelVersion]
    latest_accuracy: Optional[float]
    version_count: int
    is_ready: bool
    is_training: bool
    latest_job_id: Optional[int]


@dataclass
class ModelDetailView:
    """DTO trang chi tiết mô hình."""

    model: CnnModel
    versions: list
    production_version: Optional[ModelVersion]
    latest_job: Optional[object]
    is_ready: bool
    file_exists: bool


class ModelCatalogService:
    """Chuẩn bị context cho UI quản lý model."""

    @staticmethod
    def build_list_cards(user: User) -> list[ModelCardView]:
        """Danh sách card — đồng bộ version cũ trước khi render."""
        ModelVersionService.sync_missing_versions()
        cards = []
        for cnn in CnnModelRepository.list_for_user_with_relations(user):
            versions = list(cnn.versions.all())
            production = next((v for v in versions if v.is_production), None)
            latest_accuracy = production.accuracy_score if production else None
            if latest_accuracy is None and versions:
                latest_accuracy = versions[0].accuracy_score

            jobs = list(cnn.training_jobs.all())
            latest_job = jobs[0] if jobs else None
            is_training = bool(
                latest_job
                and latest_job.training_status
                in {
                    TrainingStatus.PENDING.value,
                    TrainingStatus.PREPARING.value,
                    TrainingStatus.TRAINING.value,
                    TrainingStatus.VALIDATING.value,
                }
            )
            is_ready = bool(cnn.model_file_path and ModelLoaderService.file_exists(cnn.model_file_path))

            cards.append(
                ModelCardView(
                    model=cnn,
                    production_version=production,
                    latest_accuracy=latest_accuracy,
                    version_count=len(versions),
                    is_ready=is_ready,
                    is_training=is_training,
                    latest_job_id=latest_job.id if latest_job else None,
                )
            )
        return cards

    @staticmethod
    def build_detail(user: User, model_id: int) -> Optional[ModelDetailView]:
        """Chi tiết một mô hình — None nếu không tồn tại."""
        ModelVersionService.sync_missing_versions()
        cnn = CnnModelRepository.get_by_id(model_id)
        if not cnn or not CnnModelRepository.user_can_access(user, cnn):
            return None

        versions = list(ModelVersionRepository.list_by_model(cnn.id))
        production = ModelVersionRepository.get_production(cnn.id)
        latest_job = cnn.training_jobs.order_by('-created_at').first()
        file_path = production.model_path if production else cnn.model_file_path
        is_ready = bool(file_path and ModelLoaderService.file_exists(file_path))

        return ModelDetailView(
            model=cnn,
            versions=versions,
            production_version=production,
            latest_job=latest_job,
            is_ready=is_ready,
            file_exists=is_ready,
        )
