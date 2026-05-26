"""Tổng hợp dữ liệu dashboard phân tích AI."""

from dataclasses import dataclass, field
from typing import Optional

from django.db.models import Avg, Count, Sum

from apps.analytics.services.chart_image_service import ChartImageService
from apps.authentication.models import User
from apps.datasets.models import DatasetClass
from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.predictions.models import Prediction
from apps.training.models import ModelMetrics, TrainingHistory
from apps.training.repositories.training_job_repository import TrainingJobRepository
from apps.training.services.training_metrics_service import TrainingMetricsService
from core.enums.training_status import TrainingStatus


@dataclass
class AnalyticsSummary:
    """Thẻ tổng quan trên dashboard."""

    total_datasets: int = 0
    total_models: int = 0
    completed_jobs: int = 0
    total_predictions: int = 0
    avg_val_accuracy: Optional[float] = None
    avg_confidence: Optional[float] = None


@dataclass
class ModelComparisonRow:
    """Một dòng so sánh model trên biểu đồ."""

    model_name: str
    job_id: int
    accuracy: float
    precision: float
    recall: float
    f1: float


@dataclass
class DistributionRow:
    """Phân bố class — dataset hoặc prediction."""

    label: str
    count: int
    percent: float


@dataclass
class TrainingChartData:
    """Dữ liệu biểu đồ accuracy/loss theo epoch."""

    labels: list[int] = field(default_factory=list)
    train_acc: list[float] = field(default_factory=list)
    val_acc: list[float] = field(default_factory=list)
    train_loss: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)


@dataclass
class ConfusionMatrixView:
    """Confusion matrix — bảng HTML + ảnh matplotlib."""

    matrix: list[list[int]] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    image_base64: Optional[str] = None
    max_value: int = 0


@dataclass
class JobOption:
    """Option chọn job huấn luyện trên dashboard."""

    job_id: int
    label: str


@dataclass
class AnalyticsDashboardView:
    """DTO đầy đủ cho trang /analytics/."""

    summary: AnalyticsSummary
    model_comparison: list[ModelComparisonRow]
    dataset_distribution: list[DistributionRow]
    prediction_distribution: list[DistributionRow]
    job_options: list[JobOption]
    selected_job_id: Optional[int]
    training_chart: TrainingChartData
    confusion: ConfusionMatrixView
    selected_job_label: str = ''


class AnalyticsDashboardService:
    """Aggregate queries cho dashboard phân tích."""

    COMPLETED = TrainingStatus.COMPLETED.value

    @classmethod
    def build_dashboard(cls, user: User, job_id: Optional[int] = None) -> AnalyticsDashboardView:
        """Dựng toàn bộ context dashboard."""
        completed_jobs = cls._completed_jobs(user)
        selected_job = cls._resolve_job(user, job_id, completed_jobs)
        metrics = selected_job.metrics.first() if selected_job else None

        return AnalyticsDashboardView(
            summary=cls._build_summary(user),
            model_comparison=cls._build_model_comparison(user),
            dataset_distribution=cls._build_dataset_distribution(user),
            prediction_distribution=cls._build_prediction_distribution(user),
            job_options=cls._build_job_options(completed_jobs),
            selected_job_id=selected_job.id if selected_job else None,
            selected_job_label=cls._job_label(selected_job) if selected_job else '',
            training_chart=cls._build_training_chart(selected_job),
            confusion=cls._build_confusion(metrics),
        )

    @staticmethod
    def _completed_jobs(user: User):
        return (
            TrainingJobRepository.list_for_user(user)
            .filter(training_status=AnalyticsDashboardService.COMPLETED)
            .select_related('model', 'dataset')
        )

    @classmethod
    def _resolve_job(cls, user: User, job_id: Optional[int], completed_jobs):
        if job_id:
            job = TrainingJobRepository.get_by_id(job_id)
            if job and TrainingJobRepository.user_can_access(user, job):
                if job.training_status == cls.COMPLETED:
                    return job
        return completed_jobs.first()

    @staticmethod
    def _build_summary(user: User) -> AnalyticsSummary:
        predictions_qs = Prediction.objects.all()
        if not user.is_admin:
            predictions_qs = predictions_qs.filter(predicted_by_id=user.id)

        completed = TrainingJobRepository.list_for_user(user).filter(
            training_status=AnalyticsDashboardService.COMPLETED
        )
        avg_acc = completed.aggregate(v=Avg('validation_accuracy'))['v']
        avg_conf = predictions_qs.aggregate(v=Avg('confidence_score'))['v']

        return AnalyticsSummary(
            total_datasets=DatasetRepository.list_for_user(user).count(),
            total_models=CnnModelRepository.list_for_user(user).count(),
            completed_jobs=completed.count(),
            total_predictions=predictions_qs.count(),
            avg_val_accuracy=round(float(avg_acc), 4) if avg_acc is not None else None,
            avg_confidence=round(float(avg_conf), 4) if avg_conf is not None else None,
        )

    @staticmethod
    def _build_model_comparison(user: User) -> list[ModelComparisonRow]:
        rows = []
        metrics_qs = ModelMetrics.objects.filter(
            training_job__training_status=AnalyticsDashboardService.COMPLETED,
        ).select_related('training_job__model')
        if not user.is_admin:
            metrics_qs = metrics_qs.filter(training_job__trained_by_id=user.id)
        metrics_qs = metrics_qs.order_by('-created_at')[:12]

        for metric in metrics_qs:
            job = metric.training_job
            rows.append(
                ModelComparisonRow(
                    model_name=job.model.model_name,
                    job_id=job.id,
                    accuracy=float(metric.accuracy or 0),
                    precision=float(metric.precision_score or 0),
                    recall=float(metric.recall_score or 0),
                    f1=float(metric.f1_score or 0),
                )
            )
        return rows

    @staticmethod
    def _build_dataset_distribution(user: User) -> list[DistributionRow]:
        dataset_ids = DatasetRepository.list_for_user(user).values_list('id', flat=True)
        grouped = (
            DatasetClass.objects.filter(dataset_id__in=dataset_ids)
            .values('class_name')
            .annotate(count=Sum('total_images'))
            .order_by('-count')
        )
        total = sum(int(row['count'] or 0) for row in grouped)
        if total <= 0:
            return []

        result = []
        for row in grouped:
            count = int(row['count'] or 0)
            if count <= 0:
                continue
            result.append(
                DistributionRow(
                    label=row['class_name'],
                    count=count,
                    percent=round(count * 100 / total, 1),
                )
            )
        return result

    @staticmethod
    def _build_prediction_distribution(user: User) -> list[DistributionRow]:
        qs = Prediction.objects.all()
        if not user.is_admin:
            qs = qs.filter(predicted_by_id=user.id)

        grouped = (
            qs.values('predicted_class')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        total = sum(row['count'] for row in grouped)
        if total <= 0:
            return []

        return [
            DistributionRow(
                label=row['predicted_class'],
                count=row['count'],
                percent=round(row['count'] * 100 / total, 1),
            )
            for row in grouped
        ]

    @staticmethod
    def _build_job_options(completed_jobs) -> list[JobOption]:
        return [
            JobOption(
                job_id=job.id,
                label=AnalyticsDashboardService._job_label(job),
            )
            for job in completed_jobs[:20]
        ]

    @staticmethod
    def _job_label(job) -> str:
        return f'#{job.id} · {job.model.model_name} ({job.dataset.dataset_name})'

    @staticmethod
    def _build_training_chart(job) -> TrainingChartData:
        if not job:
            return TrainingChartData()

        history = TrainingHistory.objects.filter(training_job_id=job.id).order_by('epoch_number')
        return TrainingChartData(
            labels=[row.epoch_number for row in history],
            train_acc=[row.train_accuracy or 0 for row in history],
            val_acc=[row.validation_accuracy or 0 for row in history],
            train_loss=[row.train_loss or 0 for row in history],
            val_loss=[row.validation_loss or 0 for row in history],
        )

    @staticmethod
    def _build_confusion(metrics: Optional[ModelMetrics]) -> ConfusionMatrixView:
        matrix, labels = TrainingMetricsService.get_confusion_data(metrics)
        if not matrix:
            return ConfusionMatrixView()

        flat_max = max(max(row) for row in matrix) if matrix else 0
        image_b64 = ChartImageService.render_confusion_matrix(matrix, labels)
        rows = [
            {'label': labels[idx], 'values': matrix[idx]}
            for idx in range(len(matrix))
        ]
        return ConfusionMatrixView(
            matrix=matrix,
            labels=labels,
            rows=rows,
            image_base64=image_b64,
            max_value=flat_max or 1,
        )

    @staticmethod
    def parse_job_id(raw) -> Optional[int]:
        """Parse job_id từ query string."""
        if not raw:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
