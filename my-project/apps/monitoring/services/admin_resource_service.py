"""Quản lý dataset/model/training/prediction — admin panel."""

from dataclasses import dataclass
from typing import Optional

from django.db.models import Q

from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.monitoring.services.admin_pagination_service import AdminPaginationService
from apps.predictions.models import Prediction
from apps.training.models import TrainingJob
from core.enums.training_status import TrainingStatus


@dataclass
class AdminActionResult:
    success: bool
    message: str


class AdminResourceService:
    """CRUD/read-only cho tài nguyên hệ thống."""

    @staticmethod
    def list_datasets(q: str = '', include_inactive: bool = True, page: int = 1):
        qs = DatasetRepository.list_all(include_inactive=include_inactive)
        if q:
            keyword = q.strip()
            qs = qs.filter(
                Q(dataset_name__icontains=keyword)
                | Q(dataset_slug__icontains=keyword)
                | Q(created_by__username__icontains=keyword)
            )
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def update_dataset(dataset_id: int, name: str, description: str, is_active: bool) -> AdminActionResult:
        dataset = DatasetRepository.get_by_id_any(dataset_id)
        if not dataset:
            return AdminActionResult(False, 'Không tìm thấy bộ dữ liệu.')
        dataset.dataset_name = name.strip()
        dataset.description = description.strip() or None
        dataset.is_active = is_active
        DatasetRepository.save(dataset)
        return AdminActionResult(True, 'Cập nhật bộ dữ liệu thành công.')

    @staticmethod
    def deactivate_dataset(dataset_id: int) -> AdminActionResult:
        dataset = DatasetRepository.get_by_id_any(dataset_id)
        if not dataset:
            return AdminActionResult(False, 'Không tìm thấy bộ dữ liệu.')
        dataset.is_active = False
        DatasetRepository.save(dataset)
        return AdminActionResult(True, 'Đã vô hiệu hóa bộ dữ liệu.')

    @staticmethod
    def list_models(q: str = '', include_inactive: bool = True, page: int = 1):
        qs = CnnModelRepository.list_all(include_inactive=include_inactive)
        if q:
            keyword = q.strip()
            qs = qs.filter(
                Q(model_name__icontains=keyword)
                | Q(model_slug__icontains=keyword)
                | Q(created_by__username__icontains=keyword)
            )
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def update_model(model_id: int, name: str, description: str, is_active: bool) -> AdminActionResult:
        model = CnnModelRepository.get_by_id_any(model_id)
        if not model:
            return AdminActionResult(False, 'Không tìm thấy mô hình.')
        model.model_name = name.strip()
        model.description = description.strip() or None
        model.is_active = is_active
        CnnModelRepository.save(model)
        return AdminActionResult(True, 'Cập nhật mô hình thành công.')

    @staticmethod
    def deactivate_model(model_id: int) -> AdminActionResult:
        model = CnnModelRepository.get_by_id_any(model_id)
        if not model:
            return AdminActionResult(False, 'Không tìm thấy mô hình.')
        model.is_active = False
        CnnModelRepository.save(model)
        return AdminActionResult(True, 'Đã vô hiệu hóa mô hình.')

    @staticmethod
    def list_training_jobs(q: str = '', status: str = '', page: int = 1):
        qs = TrainingJob.objects.select_related('model', 'dataset', 'trained_by').order_by('-created_at')
        if status:
            qs = qs.filter(training_status=status)
        if q:
            keyword = q.strip()
            qs = qs.filter(
                Q(model__model_name__icontains=keyword)
                | Q(dataset__dataset_name__icontains=keyword)
                | Q(trained_by__username__icontains=keyword)
            )
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def list_predictions(q: str = '', user_id: Optional[int] = None, page: int = 1):
        qs = Prediction.objects.select_related('model', 'predicted_by').order_by('-created_at')
        if user_id:
            qs = qs.filter(predicted_by_id=user_id)
        if q:
            keyword = q.strip()
            qs = qs.filter(
                Q(predicted_class__icontains=keyword)
                | Q(image_name__icontains=keyword)
                | Q(model__model_name__icontains=keyword)
                | Q(predicted_by__username__icontains=keyword)
            )
        return AdminPaginationService.paginate(qs, page=page)

    @staticmethod
    def training_status_choices():
        return TrainingStatus.choices()
