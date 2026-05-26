"""Repository phiên bản mô hình CNN."""

from typing import Optional

from apps.models_ai.models import ModelVersion


class ModelVersionRepository:
    """Truy vấn bảng model_versions."""

    @staticmethod
    def get_by_id(version_id: int) -> Optional[ModelVersion]:
        try:
            return ModelVersion.objects.select_related('model').get(id=version_id)
        except ModelVersion.DoesNotExist:
            return None

    @staticmethod
    def list_by_model(model_id: int):
        return ModelVersion.objects.filter(model_id=model_id).order_by('-created_at')

    @staticmethod
    def count_by_model(model_id: int) -> int:
        return ModelVersion.objects.filter(model_id=model_id).count()

    @staticmethod
    def get_production(model_id: int) -> Optional[ModelVersion]:
        return ModelVersion.objects.filter(model_id=model_id, is_production=True).first()

    @staticmethod
    def has_production(model_id: int) -> bool:
        return ModelVersion.objects.filter(model_id=model_id, is_production=True).exists()

    @staticmethod
    def path_exists(model_id: int, model_path: str) -> bool:
        return ModelVersion.objects.filter(model_id=model_id, model_path=model_path).exists()

    @staticmethod
    def create(**kwargs) -> ModelVersion:
        return ModelVersion.objects.create(**kwargs)

    @staticmethod
    def save(version: ModelVersion) -> ModelVersion:
        version.save()
        return version

    @staticmethod
    def clear_production_flags(model_id: int) -> None:
        ModelVersion.objects.filter(model_id=model_id, is_production=True).update(is_production=False)
