"""Models bộ dữ liệu — map bảng datasets, dataset_classes, dataset_images."""

from django.db import models

from apps.authentication.models import User


class Dataset(models.Model):
    """Bảng datasets — metadata bộ dữ liệu huấn luyện CNN."""

    dataset_name = models.CharField(max_length=100, verbose_name='Tên bộ dữ liệu')
    dataset_slug = models.CharField(max_length=100, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    dataset_path = models.CharField(max_length=500, verbose_name='Đường dẫn lưu trữ')
    total_images = models.IntegerField(default=0, verbose_name='Tổng ảnh')
    total_classes = models.IntegerField(default=0, verbose_name='Tổng class')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='created_by',
        related_name='datasets',
        verbose_name='Người tạo',
    )
    is_active = models.BooleanField(default=True, verbose_name='Kích hoạt')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'datasets'
        verbose_name = 'Bộ dữ liệu'
        verbose_name_plural = 'Bộ dữ liệu'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.dataset_name


class DatasetClass(models.Model):
    """Bảng dataset_classes — nhãn/class trong dataset."""

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        db_column='dataset_id',
        related_name='classes',
        verbose_name='Bộ dữ liệu',
    )
    class_name = models.CharField(max_length=100, verbose_name='Tên class')
    class_slug = models.CharField(max_length=100, blank=True, null=True, verbose_name='Slug class')
    total_images = models.IntegerField(default=0, verbose_name='Số ảnh')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'dataset_classes'
        verbose_name = 'Class dataset'
        verbose_name_plural = 'Class dataset'
        ordering = ['class_name']

    def __str__(self) -> str:
        return self.class_name


class DatasetImage(models.Model):
    """Bảng dataset_images — metadata ảnh thuộc dataset."""

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        db_column='dataset_id',
        related_name='images',
        verbose_name='Bộ dữ liệu',
    )
    dataset_class = models.ForeignKey(
        DatasetClass,
        on_delete=models.CASCADE,
        db_column='class_id',
        related_name='images',
        verbose_name='Class',
    )
    image_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Tên file')
    image_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='URL ảnh')
    image_format = models.CharField(max_length=20, blank=True, null=True, verbose_name='Định dạng')
    mime_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='MIME type')
    width = models.IntegerField(blank=True, null=True, verbose_name='Chiều rộng')
    height = models.IntegerField(blank=True, null=True, verbose_name='Chiều cao')
    channels = models.IntegerField(blank=True, null=True, verbose_name='Kênh màu')
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name='Dung lượng')
    is_train = models.BooleanField(default=True, verbose_name='Tập huấn luyện')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'dataset_images'
        verbose_name = 'Ảnh dataset'
        verbose_name_plural = 'Ảnh dataset'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.image_name or str(self.id)
