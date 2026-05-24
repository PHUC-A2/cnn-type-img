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

    @staticmethod
    def list_paths_for_training(dataset_id: int):
        """Lấy metadata ảnh để build thư mục train/val."""
        rows = DatasetImage.objects.filter(dataset_id=dataset_id).select_related('dataset_class')
        return [
            {
                'image_url': row.image_url,
                'image_name': row.image_name,
                'class_name': row.dataset_class.class_name,
                'is_train': row.is_train,
            }
            for row in rows
            if row.image_url and row.image_name
        ]
