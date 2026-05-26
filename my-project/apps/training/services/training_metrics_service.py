"""Lưu metrics đánh giá sau huấn luyện — sklearn + confusion matrix."""

import random
from typing import Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from apps.training.models import ModelMetrics, TrainingJob


class TrainingMetricsService:
    """Tạo bản ghi ModelMetrics kèm confusion matrix."""

    @staticmethod
    def save_from_predictions(
        job: TrainingJob,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_labels: list[str],
    ) -> ModelMetrics:
        """Lưu metrics thật từ kết quả predict trên tập validation."""
        labels_idx = list(range(len(class_labels)))
        cm = confusion_matrix(y_true, y_pred, labels=labels_idx)
        accuracy = float(accuracy_score(y_true, y_pred))
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true,
            y_pred,
            average='weighted',
            zero_division=0,
        )

        return ModelMetrics.objects.create(
            training_job=job,
            accuracy=round(accuracy, 4),
            precision_score=round(float(precision), 4),
            recall_score=round(float(recall), 4),
            f1_score=round(float(f1), 4),
            confusion_matrix_json=cm.tolist(),
            class_labels_json=class_labels,
        )

    @staticmethod
    def save_simulation(job: TrainingJob) -> ModelMetrics:
        """Sinh confusion matrix mô phỏng theo class của dataset."""
        class_labels = list(job.dataset.classes.values_list('class_name', flat=True))
        if not class_labels:
            class_labels = ['class_a', 'class_b']

        rng = random.Random(job.id)
        n = len(class_labels)
        matrix = [[0] * n for _ in range(n)]

        for row_idx in range(n):
            correct = rng.randint(12, 22)
            matrix[row_idx][row_idx] = correct
            remaining = rng.randint(2, 8)
            for col_idx in range(n):
                if col_idx == row_idx:
                    continue
                share = rng.randint(0, remaining)
                matrix[row_idx][col_idx] = share
                remaining -= share

        y_true: list[int] = []
        y_pred: list[int] = []
        for true_idx, row in enumerate(matrix):
            for pred_idx, count in enumerate(row):
                y_true.extend([true_idx] * count)
                y_pred.extend([pred_idx] * count)

        accuracy = job.validation_accuracy or job.train_accuracy or 0.0
        if y_true and y_pred:
            accuracy = float(accuracy_score(y_true, y_pred))
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_true,
                y_pred,
                average='weighted',
                zero_division=0,
            )
        else:
            precision = recall = f1 = accuracy

        return ModelMetrics.objects.create(
            training_job=job,
            accuracy=round(float(accuracy), 4),
            precision_score=round(float(precision), 4),
            recall_score=round(float(recall), 4),
            f1_score=round(float(f1), 4),
            confusion_matrix_json=matrix,
            class_labels_json=class_labels,
        )

    @staticmethod
    def save_fallback(job: TrainingJob) -> ModelMetrics:
        """Fallback khi không có dữ liệu đánh giá chi tiết."""
        acc = job.validation_accuracy or job.train_accuracy or 0.0
        return ModelMetrics.objects.create(
            training_job=job,
            accuracy=acc,
            precision_score=acc,
            recall_score=acc,
            f1_score=acc,
        )

    @staticmethod
    def get_confusion_data(metrics: Optional[ModelMetrics]) -> tuple[list[list[int]], list[str]]:
        """Trả về matrix + labels từ bản ghi metrics."""
        if not metrics or not metrics.confusion_matrix_json:
            return [], []
        labels = metrics.class_labels_json or []
        matrix = metrics.confusion_matrix_json or []
        return matrix, labels
