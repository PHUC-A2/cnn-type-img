"""Repository thao tác bảng dataset_images."""

from apps.datasets.models import DatasetImage


class DatasetImageRepository:
    """Truy vấn DB cho DatasetImage."""

    @staticmethod
    def bulk_create(images: list) -> list:
        return DatasetImage.objects.bulk_create(images)

    @staticmethod
    def sample_by_dataset(dataset_id: int, limit: int = 12):
        return DatasetImage.objects.filter(dataset_id=dataset_id).select_related('dataset_class')[:limit]

    @staticmethod
    def count_train_val(dataset_id: int) -> dict:
        qs = DatasetImage.objects.filter(dataset_id=dataset_id)
        train = qs.filter(is_train=True).count()
        val = qs.filter(is_train=False).count()
        return {'train': train, 'val': val}
