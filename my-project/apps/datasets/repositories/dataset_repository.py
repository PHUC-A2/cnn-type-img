"""Repository thao tác bảng datasets."""

from typing import Optional

from apps.authentication.models import User
from apps.datasets.models import Dataset


class DatasetRepository:
    """Truy vấn DB cho Dataset."""

    @staticmethod
    def get_by_id(dataset_id: int) -> Optional[Dataset]:
        try:
            return Dataset.objects.get(id=dataset_id, is_active=True)
        except Dataset.DoesNotExist:
            return None

    @staticmethod
    def get_by_id_any(dataset_id: int) -> Optional[Dataset]:
        """Lấy dataset kể cả inactive — admin panel."""
        try:
            return Dataset.objects.select_related('created_by').get(id=dataset_id)
        except Dataset.DoesNotExist:
            return None

    @staticmethod
    def list_all(include_inactive: bool = False):
        """Danh sách toàn bộ dataset — admin."""
        qs = Dataset.objects.select_related('created_by').order_by('-created_at')
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Dataset]:
        try:
            return Dataset.objects.get(dataset_slug=slug, is_active=True)
        except Dataset.DoesNotExist:
            return None

    @staticmethod
    def slug_exists(slug: str) -> bool:
        return Dataset.objects.filter(dataset_slug=slug).exists()

    @staticmethod
    def list_for_user(user: User):
        """User thường chỉ thấy dataset của mình; admin thấy tất cả."""
        qs = Dataset.objects.filter(is_active=True).select_related('created_by')
        if not user.is_admin:
            qs = qs.filter(created_by_id=user.id)
        return qs

    @staticmethod
    def create(**kwargs) -> Dataset:
        return Dataset.objects.create(**kwargs)

    @staticmethod
    def save(dataset: Dataset) -> Dataset:
        dataset.save()
        return dataset

    @staticmethod
    def user_can_access(user: User, dataset: Dataset) -> bool:
        return user.is_admin or dataset.created_by_id == user.id
