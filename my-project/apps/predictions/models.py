"""Models phân loại ảnh — predictions, prediction_probabilities, image_preprocessing_logs."""

from django.db import models

from apps.authentication.models import User
from apps.models_ai.models import CnnModel


class Prediction(models.Model):
    """Kết quả phân loại ảnh bằng CNN."""

    model = models.ForeignKey(
        CnnModel,
        on_delete=models.CASCADE,
        db_column='model_id',
        related_name='predictions',
        verbose_name='Mô hình',
    )
    predicted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='predicted_by',
        related_name='predictions',
        verbose_name='Người dự đoán',
    )
    image_name = models.CharField(max_length=255, verbose_name='Tên ảnh')
    image_url = models.CharField(max_length=500, verbose_name='URL ảnh')
    predicted_class = models.CharField(max_length=100, verbose_name='Nhãn dự đoán')
    confidence_score = models.FloatField(verbose_name='Độ tin cậy')
    top_k = models.IntegerField(default=3, verbose_name='Top-K')
    inference_time_ms = models.FloatField(blank=True, null=True, verbose_name='Thời gian inference (ms)')
    is_simulation = models.BooleanField(default=False, verbose_name='Chế độ mô phỏng')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'predictions'
        verbose_name = 'Dự đoán'
        verbose_name_plural = 'Dự đoán'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.predicted_class} ({self.confidence_score:.4f})'


class PredictionProbability(models.Model):
    """Xác suất từng class cho một lần dự đoán."""

    prediction = models.ForeignKey(
        Prediction,
        on_delete=models.CASCADE,
        db_column='prediction_id',
        related_name='probabilities',
        verbose_name='Dự đoán',
    )
    class_name = models.CharField(max_length=100, verbose_name='Tên class')
    probability = models.FloatField(verbose_name='Xác suất')
    rank_order = models.IntegerField(verbose_name='Thứ hạng')

    class Meta:
        db_table = 'prediction_probabilities'
        verbose_name = 'Xác suất class'
        verbose_name_plural = 'Xác suất class'
        ordering = ['rank_order']

    def __str__(self) -> str:
        return f'{self.class_name}: {self.probability:.4f}'


class ImagePreprocessingLog(models.Model):
    """Log tiền xử lý ảnh trước inference."""

    prediction = models.OneToOneField(
        Prediction,
        on_delete=models.CASCADE,
        db_column='prediction_id',
        related_name='preprocess_log',
        verbose_name='Dự đoán',
    )
    original_width = models.IntegerField(verbose_name='Chiều rộng gốc')
    original_height = models.IntegerField(verbose_name='Chiều cao gốc')
    target_width = models.IntegerField(verbose_name='Chiều rộng resize')
    target_height = models.IntegerField(verbose_name='Chiều cao resize')
    channels = models.IntegerField(default=3, verbose_name='Kênh màu')
    normalize_scale = models.FloatField(default=0.003921568627451, verbose_name='Hệ số chuẩn hóa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'image_preprocessing_logs'
        verbose_name = 'Log tiền xử lý ảnh'
        verbose_name_plural = 'Log tiền xử lý ảnh'

    def __str__(self) -> str:
        return f'Preprocess #{self.prediction_id}'
