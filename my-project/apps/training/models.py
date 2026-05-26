"""Models huấn luyện — training_jobs, training_history, model_metrics."""

from django.db import models

from apps.authentication.models import User
from apps.datasets.models import Dataset
from apps.models_ai.models import CnnModel
from core.enums.training_status import TrainingStatus


class TrainingJob(models.Model):
    """Job huấn luyện CNN."""

    model = models.ForeignKey(
        CnnModel,
        on_delete=models.CASCADE,
        db_column='model_id',
        related_name='training_jobs',
        verbose_name='Mô hình',
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        db_column='dataset_id',
        related_name='training_jobs',
        verbose_name='Bộ dữ liệu',
    )
    trained_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='trained_by',
        related_name='training_jobs',
        verbose_name='Người huấn luyện',
    )
    training_status = models.CharField(
        max_length=20,
        choices=TrainingStatus.choices(),
        default=TrainingStatus.PENDING.value,
        verbose_name='Trạng thái',
    )
    status_message = models.TextField(blank=True, null=True, verbose_name='Thông báo trạng thái')
    epochs = models.IntegerField(default=10, verbose_name='Số epoch')
    batch_size = models.IntegerField(default=16, verbose_name='Batch size')
    learning_rate = models.FloatField(default=0.001, verbose_name='Learning rate')
    optimizer = models.CharField(max_length=50, default='adam', verbose_name='Optimizer')
    loss_function = models.CharField(
        max_length=100,
        default='categorical_crossentropy',
        verbose_name='Loss function',
    )
    train_accuracy = models.FloatField(blank=True, null=True, verbose_name='Train accuracy')
    validation_accuracy = models.FloatField(blank=True, null=True, verbose_name='Val accuracy')
    train_loss = models.FloatField(blank=True, null=True, verbose_name='Train loss')
    validation_loss = models.FloatField(blank=True, null=True, verbose_name='Val loss')
    execution_time = models.FloatField(blank=True, null=True, verbose_name='Thời gian (s)')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='Bắt đầu')
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name='Kết thúc')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'training_jobs'
        verbose_name = 'Job huấn luyện'
        verbose_name_plural = 'Job huấn luyện'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Job #{self.id} — {self.model.model_name}'

    def get_status_display_vi(self) -> str:
        try:
            return TrainingStatus(self.training_status).label_vi()
        except ValueError:
            return self.training_status


class TrainingHistory(models.Model):
    """Accuracy/loss theo từng epoch."""

    training_job = models.ForeignKey(
        TrainingJob,
        on_delete=models.CASCADE,
        db_column='training_job_id',
        related_name='history',
        verbose_name='Job',
    )
    epoch_number = models.IntegerField(verbose_name='Epoch')
    train_accuracy = models.FloatField(blank=True, null=True, verbose_name='Train accuracy')
    validation_accuracy = models.FloatField(blank=True, null=True, verbose_name='Val accuracy')
    train_loss = models.FloatField(blank=True, null=True, verbose_name='Train loss')
    validation_loss = models.FloatField(blank=True, null=True, verbose_name='Val loss')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'training_history'
        verbose_name = 'Lịch sử epoch'
        verbose_name_plural = 'Lịch sử epoch'
        ordering = ['epoch_number']

    def __str__(self) -> str:
        return f'Epoch {self.epoch_number}'


class ModelMetrics(models.Model):
    """Metrics đánh giá sau huấn luyện."""

    training_job = models.ForeignKey(
        TrainingJob,
        on_delete=models.CASCADE,
        db_column='training_job_id',
        related_name='metrics',
        verbose_name='Job',
    )
    accuracy = models.FloatField(blank=True, null=True, verbose_name='Accuracy')
    precision_score = models.FloatField(blank=True, null=True, verbose_name='Precision')
    recall_score = models.FloatField(blank=True, null=True, verbose_name='Recall')
    f1_score = models.FloatField(blank=True, null=True, verbose_name='F1 score')
    confusion_matrix_json = models.JSONField(blank=True, null=True, verbose_name='Confusion matrix')
    class_labels_json = models.JSONField(blank=True, null=True, verbose_name='Nhãn class')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'model_metrics'
        verbose_name = 'Metrics mô hình'
        verbose_name_plural = 'Metrics mô hình'

    def __str__(self) -> str:
        return f'Metrics job #{self.training_job_id}'
