"""Repository bảng predictions."""

from typing import Optional

from apps.authentication.models import User
from apps.predictions.models import ImagePreprocessingLog, Prediction, PredictionProbability


class PredictionRepository:
    """Truy vấn và lưu kết quả phân loại."""

    @staticmethod
    def get_by_id(prediction_id: int) -> Optional[Prediction]:
        try:
            return Prediction.objects.select_related(
                'model', 'predicted_by', 'preprocess_log'
            ).get(id=prediction_id)
        except Prediction.DoesNotExist:
            return None

    @staticmethod
    def create(**kwargs) -> Prediction:
        return Prediction.objects.create(**kwargs)

    @staticmethod
    def list_for_user(user: User):
        qs = Prediction.objects.select_related('model', 'predicted_by').order_by('-created_at')
        if not user.is_admin:
            qs = qs.filter(predicted_by_id=user.id)
        return qs

    @staticmethod
    def user_can_access(user: User, prediction: Prediction) -> bool:
        return user.is_admin or prediction.predicted_by_id == user.id

    @staticmethod
    def bulk_create_probabilities(rows: list) -> list:
        return PredictionProbability.objects.bulk_create(rows)

    @staticmethod
    def create_preprocess_log(**kwargs) -> ImagePreprocessingLog:
        return ImagePreprocessingLog.objects.create(**kwargs)

    @staticmethod
    def get_probabilities(prediction_id: int):
        return PredictionProbability.objects.filter(prediction_id=prediction_id).order_by('rank_order')
