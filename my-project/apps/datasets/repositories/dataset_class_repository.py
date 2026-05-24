"""Repository thao tác bảng dataset_classes."""

from apps.datasets.models import DatasetClass


class DatasetClassRepository:
    """Truy vấn DB cho DatasetClass."""

    @staticmethod
    def bulk_create(classes: list) -> list:
        return DatasetClass.objects.bulk_create(classes)

    @staticmethod
    def list_by_dataset(dataset_id: int):
        return DatasetClass.objects.filter(dataset_id=dataset_id).order_by('class_name')
