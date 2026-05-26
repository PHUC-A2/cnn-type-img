"""Orchestrator phân loại ảnh — lưu DB + gọi CNN predictor."""

from dataclasses import dataclass
from typing import Optional

from django.core.files.uploadedfile import UploadedFile

from apps.authentication.models import User
from apps.datasets.repositories.dataset_class_repository import DatasetClassRepository
from apps.models_ai.models import CnnModel
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.models_ai.services.model_loader_service import ModelLoaderService
from apps.models_ai.services.model_version_service import ModelVersionService
from apps.predictions.models import Prediction, PredictionProbability
from apps.predictions.repositories.prediction_repository import PredictionRepository
from apps.predictions.services.cnn.predictor import CnnPredictorService
from apps.predictions.services.prediction_storage_service import PredictionStorageService
from apps.training.models import TrainingJob
from core.enums.training_status import TrainingStatus


@dataclass
class PredictionRunResult:
    """Kết quả chạy phân loại."""

    success: bool
    message: str
    prediction: Optional[Prediction] = None


class PredictionService:
    """Service nghiệp vụ phân loại ảnh Phase 5."""

    @staticmethod
    def list_ready_models(user: User):
        """Mô hình có file production sẵn sàng predict."""
        ModelVersionService.sync_missing_versions()
        ready = []
        for cnn in CnnModelRepository.list_for_user(user):
            version = ModelVersionRepository.get_production(cnn.id)
            path = version.model_path if version else cnn.model_file_path
            if path and ModelLoaderService.file_exists(path):
                try:
                    PredictionService.resolve_class_labels(cnn)
                    ready.append(cnn)
                except ValueError:
                    continue
        return ready

    @staticmethod
    def resolve_class_labels(cnn_model: CnnModel) -> list[str]:
        """Lấy nhãn class theo thứ tự alphabet — khớp Keras flow_from_directory."""
        job = (
            TrainingJob.objects.filter(
                model_id=cnn_model.id,
                training_status=TrainingStatus.COMPLETED.value,
            )
            .order_by('-finished_at', '-id')
            .first()
        )
        if not job:
            raise ValueError('Không tìm thấy job huấn luyện hoàn thành cho mô hình này.')

        classes = DatasetClassRepository.list_by_dataset(job.dataset_id)
        names = [item.class_name for item in classes]
        if not names:
            raise ValueError('Bộ dữ liệu huấn luyện không có class.')
        return sorted(names)

    @staticmethod
    def run_prediction(
        user: User,
        model_id: int,
        image_file: UploadedFile,
        top_k: int = 3,
    ) -> PredictionRunResult:
        """Upload ảnh, chạy inference và lưu kết quả."""
        cnn = CnnModelRepository.get_by_id(model_id)
        if not cnn or not CnnModelRepository.user_can_access(user, cnn):
            return PredictionRunResult(False, 'Không tìm thấy mô hình hoặc bạn không có quyền sử dụng.')

        try:
            class_labels = PredictionService.resolve_class_labels(cnn)
            image_name, image_url = PredictionStorageService.save_image(image_file, user.id)
            image_path = PredictionStorageService.resolve_path(image_url)
            inference = CnnPredictorService.predict(cnn, image_path, class_labels, top_k=top_k)
        except ValueError as exc:
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.warning('prediction', str(exc), context={'model_id': model_id, 'user_id': user.id})
            return PredictionRunResult(False, str(exc))
        except Exception as exc:
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.error(
                'prediction',
                f'Phân loại thất bại model #{model_id}',
                exc=exc,
                context={'model_id': model_id, 'user_id': user.id},
            )
            return PredictionRunResult(False, f'Phân loại thất bại: {exc}')

        prediction = PredictionRepository.create(
            model=cnn,
            predicted_by=user,
            image_name=image_name,
            image_url=image_url,
            predicted_class=inference.predicted_class,
            confidence_score=inference.confidence_score,
            top_k=top_k,
            inference_time_ms=inference.inference_time_ms,
            is_simulation=inference.is_simulation,
        )

        probability_rows = [
            PredictionProbability(
                prediction=prediction,
                class_name=score.class_name,
                probability=score.probability,
                rank_order=rank,
            )
            for rank, score in enumerate(inference.scores, start=1)
        ]
        PredictionRepository.bulk_create_probabilities(probability_rows)

        meta = inference.preprocess_meta
        PredictionRepository.create_preprocess_log(
            prediction=prediction,
            original_width=meta.original_width,
            original_height=meta.original_height,
            target_width=meta.target_width,
            target_height=meta.target_height,
            channels=meta.channels,
            normalize_scale=meta.normalize_scale,
        )

        mode = ' (mô phỏng)' if inference.is_simulation else ''
        from apps.monitoring.services.system_log_service import SystemLogService
        SystemLogService.info(
            'prediction',
            f'Phân loại thành công{mode}: {inference.predicted_class}',
            context={
                'prediction_id': prediction.id,
                'model_id': cnn.id,
                'user_id': user.id,
                'inference_time_ms': inference.inference_time_ms,
                'confidence': inference.confidence_score,
            },
        )
        return PredictionRunResult(
            success=True,
            message=f'Phân loại thành công{mode}.',
            prediction=prediction,
        )
