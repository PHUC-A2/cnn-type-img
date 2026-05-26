"""Repository mô hình CNN."""

from typing import Optional

from django.db.models import Prefetch

from apps.authentication.models import User
from apps.models_ai.models import CnnModel
from apps.training.models import TrainingJob


class CnnModelRepository:
    """Truy vấn bảng cnn_models."""

    @staticmethod
    def get_by_id(model_id: int) -> Optional[CnnModel]:
        try:
            return CnnModel.objects.get(id=model_id, is_active=True)
        except CnnModel.DoesNotExist:
            return None

    @staticmethod
    def slug_exists(slug: str) -> bool:
        return CnnModel.objects.filter(model_slug=slug).exists()

    @staticmethod
    def create(**kwargs) -> CnnModel:
        return CnnModel.objects.create(**kwargs)

    @staticmethod
    def save(model: CnnModel) -> CnnModel:
        model.save()
        return model

    @staticmethod
    def list_for_user(user: User):
        qs = CnnModel.objects.filter(is_active=True).select_related('created_by')
        if not user.is_admin:
            qs = qs.filter(created_by_id=user.id)
        return qs

    @staticmethod
    def user_can_access(user: User, model: CnnModel) -> bool:
        """Kiểm tra quyền xem/sửa mô hình."""
        return user.is_admin or model.created_by_id == user.id

    @staticmethod
    def list_for_user_with_relations(user: User):
        """Danh sách mô hình kèm phiên bản và job huấn luyện."""
        qs = (
            CnnModel.objects.filter(is_active=True)
            .select_related('created_by')
            .prefetch_related(
                'versions',
                Prefetch(
                    'training_jobs',
                    queryset=TrainingJob.objects.order_by('-created_at'),
                ),
            )
        )
        if not user.is_admin:
            qs = qs.filter(created_by_id=user.id)
        return qs.order_by('-created_at')
