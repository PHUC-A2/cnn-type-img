"""Chuyển kết quả phân loại sang câu mô tả dễ hiểu cho người dùng."""

from dataclasses import dataclass

from apps.predictions.models import Prediction, PredictionProbability


# Ánh xạ tên class phổ biến → nhãn tiếng Việt dễ đọc
_CLASS_LABEL_VI: dict[str, str] = {
    'dog': 'Con chó',
    'cat': 'Con mèo',
    'bird': 'Con chim',
    'chim': 'Con chim',
    'cho': 'Con chó',
    'chó': 'Con chó',
    'meo': 'Con mèo',
    'mèo': 'Con mèo',
    'person': 'Con người',
    'human': 'Con người',
    'people': 'Con người',
    'nguoi': 'Con người',
    'người': 'Con người',
    'man': 'Người đàn ông',
    'woman': 'Người phụ nữ',
    'horse': 'Con ngựa',
    'cow': 'Con bò',
    'car': 'Xe ô tô',
    'flower': 'Hoa',
    'hoa': 'Hoa',
}

# Từ khóa suy luận nhóm đối tượng lớn
_ANIMAL_KEYWORDS = (
    'dog', 'cat', 'bird', 'chim', 'cho', 'chó', 'meo', 'mèo',
    'animal', 'pet', 'dong vat', 'động vật', 'horse', 'cow', 'fish', 'ca', 'cá',
)
_PERSON_KEYWORDS = (
    'person', 'human', 'people', 'nguoi', 'người', 'man', 'woman', 'face', 'khuon mat',
)


@dataclass
class ClassAlternativeDisplay:
    """Một class trong Top-K — dùng so sánh trên giao diện."""

    class_name: str
    display_name: str
    percent: float
    is_winner: bool
    comparison_text: str


@dataclass
class PredictionResultDisplay:
    """Bộ thông tin hiển thị kết luận phân loại."""

    verdict_label: str
    category_label: str
    confidence_percent: float
    summary_sentence: str
    alternatives: list[ClassAlternativeDisplay]


class PredictionDisplayService:
    """Service tạo mô tả kết quả phân loại bằng tiếng Việt."""

    @staticmethod
    def _normalize_key(class_name: str) -> str:
        return class_name.strip().lower().replace('_', ' ').replace('-', ' ')

    @staticmethod
    def format_class_label(class_name: str) -> str:
        """Chuyển tên class dataset sang nhãn tiếng Việt nếu có trong bảng ánh xạ."""
        key = PredictionDisplayService._normalize_key(class_name)
        if key in _CLASS_LABEL_VI:
            return _CLASS_LABEL_VI[key]
        # Giữ nguyên tên gốc nhưng viết hoa chữ cái đầu
        return class_name.strip().title()

    @staticmethod
    def infer_category(class_name: str) -> str:
        """Suy luận nhóm đối tượng lớn từ tên class."""
        key = PredictionDisplayService._normalize_key(class_name)
        if any(word in key for word in _PERSON_KEYWORDS):
            return 'Con người'
        if any(word in key for word in _ANIMAL_KEYWORDS):
            return 'Động vật'
        return 'Đối tượng trong dataset'

    @staticmethod
    def build_comparison_text(display_name: str, percent: float, is_winner: bool) -> str:
        """Tạo câu so sánh cho từng class."""
        if is_winner:
            return f'Ảnh thuộc nhóm «{display_name}» — {percent:.1f}%'
        return f'Không phải «{display_name}» — chỉ {percent:.1f}%'

    @staticmethod
    def build_from_prediction(
        prediction: Prediction,
        probabilities: list[PredictionProbability] | None = None,
    ) -> PredictionResultDisplay:
        """Tạo context hiển thị từ bản ghi prediction."""
        if probabilities is None:
            probabilities = list(prediction.probabilities.all())

        winner_label = PredictionDisplayService.format_class_label(prediction.predicted_class)
        category = PredictionDisplayService.infer_category(prediction.predicted_class)
        confidence_percent = round(float(prediction.confidence_score) * 100, 1)

        summary = (
            f'Mô hình CNN cho rằng ảnh trên là {winner_label.lower()} '
            f'(class «{prediction.predicted_class}»), thuộc nhóm {category.lower()}, '
            f'với độ tin cậy {confidence_percent}%.'
        )

        alternatives: list[ClassAlternativeDisplay] = []
        for prob in probabilities:
            display_name = PredictionDisplayService.format_class_label(prob.class_name)
            percent = round(float(prob.probability) * 100, 1)
            is_winner = prob.class_name == prediction.predicted_class
            alternatives.append(
                ClassAlternativeDisplay(
                    class_name=prob.class_name,
                    display_name=display_name,
                    percent=percent,
                    is_winner=is_winner,
                    comparison_text=PredictionDisplayService.build_comparison_text(
                        display_name, percent, is_winner,
                    ),
                )
            )

        return PredictionResultDisplay(
            verdict_label=winner_label,
            category_label=category,
            confidence_percent=confidence_percent,
            summary_sentence=summary,
            alternatives=alternatives,
        )
