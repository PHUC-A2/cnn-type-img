"""Chuyển kết quả phân loại sang câu mô tả tiếng Việt dễ hiểu."""

from dataclasses import dataclass

from apps.datasets.repositories.dataset_class_repository import DatasetClassRepository
from apps.models_ai.models import CnnModel
from apps.predictions.models import Prediction, PredictionProbability
from apps.training.models import TrainingJob
from core.enums.training_status import TrainingStatus
from core.i18n.class_label_vi import (
    build_label_map,
    infer_object_category,
    suggest_vietnamese_label,
)


@dataclass
class ClassAlternativeDisplay:
    """Một class trong Top-K — dùng so sánh trên giao diện."""

    class_name: str
    display_name: str
    display_name_vi: str
    percent: float
    is_winner: bool
    comparison_text: str


@dataclass
class PredictionResultDisplay:
    """Bộ thông tin hiển thị kết luận phân loại."""

    verdict_label: str
    verdict_label_vi: str
    category_label: str
    confidence_percent: float
    summary_sentence: str
    alternatives: list[ClassAlternativeDisplay]


class PredictionDisplayService:
    """Service tạo mô tả kết quả phân loại bằng tiếng Việt."""

    @staticmethod
    def resolve_label_map_for_model(cnn_model: CnnModel) -> dict[str, str]:
        """Lấy map nhãn tiếng Việt từ dataset đã huấn luyện model."""
        job = (
            TrainingJob.objects.filter(
                model_id=cnn_model.id,
                training_status=TrainingStatus.COMPLETED.value,
            )
            .order_by('-finished_at', '-id')
            .first()
        )
        if not job:
            return {}

        classes = DatasetClassRepository.list_by_dataset(job.dataset_id)
        names = [item.class_name for item in classes]
        return build_label_map(names)

    @staticmethod
    def format_class_label(class_name: str, label_map: dict[str, str] | None = None) -> str:
        if label_map and class_name in label_map:
            return label_map[class_name]
        return suggest_vietnamese_label(class_name)

    @staticmethod
    def build_comparison_text(display_name_vi: str, percent: float, is_winner: bool) -> str:
        if is_winner:
            return f'Ảnh thuộc nhóm «{display_name_vi}» — {percent:.1f}%'
        return f'Không phải «{display_name_vi}» — chỉ {percent:.1f}%'

    @staticmethod
    def build_from_prediction(
        prediction: Prediction,
        probabilities: list[PredictionProbability] | None = None,
        label_map: dict[str, str] | None = None,
    ) -> PredictionResultDisplay:
        if probabilities is None:
            probabilities = list(prediction.probabilities.all())

        if label_map is None:
            label_map = PredictionDisplayService.resolve_label_map_for_model(prediction.model)

        winner_vi = PredictionDisplayService.format_class_label(
            prediction.predicted_class, label_map,
        )
        category = infer_object_category(prediction.predicted_class, winner_vi)
        confidence_percent = round(float(prediction.confidence_score) * 100, 1)

        summary = (
            f'Mô hình CNN nhận diện ảnh trên là {winner_vi} '
            f'(class gốc: «{prediction.predicted_class}»), thuộc nhóm {category.lower()}, '
            f'với độ tin cậy {confidence_percent}%.'
        )

        alternatives: list[ClassAlternativeDisplay] = []
        for prob in probabilities:
            display_vi = PredictionDisplayService.format_class_label(prob.class_name, label_map)
            percent = round(float(prob.probability) * 100, 1)
            is_winner = prob.class_name == prediction.predicted_class
            alternatives.append(
                ClassAlternativeDisplay(
                    class_name=prob.class_name,
                    display_name=prob.class_name,
                    display_name_vi=display_vi,
                    percent=percent,
                    is_winner=is_winner,
                    comparison_text=PredictionDisplayService.build_comparison_text(
                        display_vi, percent, is_winner,
                    ),
                )
            )

        return PredictionResultDisplay(
            verdict_label=prediction.predicted_class,
            verdict_label_vi=winner_vi,
            category_label=category,
            confidence_percent=confidence_percent,
            summary_sentence=summary,
            alternatives=alternatives,
        )
