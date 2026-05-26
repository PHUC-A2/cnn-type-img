"""Model CNN — bảng cnn_models."""

from django.db import models

from apps.authentication.models import User


class CnnModel(models.Model):
    """Metadata mô hình CNN đã huấn luyện."""

    model_name = models.CharField(max_length=100, verbose_name='Tên mô hình')
    model_slug = models.CharField(max_length=100, unique=True, verbose_name='Slug')
    architecture_type = models.CharField(
        max_length=100,
        default='cnn_basic',
        verbose_name='Kiến trúc',
    )
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    framework = models.CharField(max_length=50, default='tensorflow', verbose_name='Framework')
    input_width = models.IntegerField(default=128, verbose_name='Chiều rộng input')
    input_height = models.IntegerField(default=128, verbose_name='Chiều cao input')
    channels = models.IntegerField(default=3, verbose_name='Kênh màu')
    total_parameters = models.BigIntegerField(blank=True, null=True, verbose_name='Số tham số')
    model_file_path = models.CharField(max_length=500, blank=True, null=True, verbose_name='Đường dẫn file')
    model_size_mb = models.FloatField(blank=True, null=True, verbose_name='Dung lượng MB')
    version = models.CharField(max_length=50, default='1.0.0', verbose_name='Phiên bản')
    is_active = models.BooleanField(default=True, verbose_name='Kích hoạt')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='created_by',
        related_name='cnn_models',
        verbose_name='Người tạo',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'cnn_models'
        verbose_name = 'Mô hình CNN'
        verbose_name_plural = 'Mô hình CNN'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.model_name


class ModelVersion(models.Model):
    """Phiên bản file .h5 của mô hình CNN — bảng model_versions."""

    model = models.ForeignKey(
        CnnModel,
        on_delete=models.CASCADE,
        db_column='model_id',
        related_name='versions',
        verbose_name='Mô hình',
    )
    version_name = models.CharField(max_length=100, verbose_name='Tên phiên bản')
    version_number = models.CharField(max_length=50, verbose_name='Số phiên bản')
    model_path = models.CharField(max_length=500, verbose_name='Đường dẫn file')
    accuracy_score = models.FloatField(blank=True, null=True, verbose_name='Độ chính xác')
    is_production = models.BooleanField(default=False, verbose_name='Đang dùng production')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'model_versions'
        verbose_name = 'Phiên bản mô hình'
        verbose_name_plural = 'Phiên bản mô hình'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.model.model_name} — {self.version_number}'
