"""CNN inference — predict softmax probabilities."""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from apps.models_ai.models import CnnModel
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.models_ai.services.model_loader_service import ModelLoaderService
from apps.predictions.services.cnn.image_preprocessor import InferenceImagePreprocessor
from core.ml.dependencies import check_tensorflow


@dataclass
class ClassScore:
    """Điểm xác suất một class."""

    class_name: str
    probability: float


@dataclass
class InferenceResult:
    """Kết quả inference CNN."""

    predicted_class: str
    confidence_score: float
    scores: list
    preprocess_meta: object
    inference_time_ms: float
    is_simulation: bool


class CnnPredictorService:
    """Chạy inference thật hoặc mô phỏng."""

    SIMULATION_MARKER = 'SIMULATED_MODEL_PLACEHOLDER'

    @classmethod
    def predict(
        cls,
        cnn_model: CnnModel,
        image_path: Path,
        class_labels: list[str],
        top_k: int = 3,
    ) -> InferenceResult:
        """Dự đoán nhãn ảnh bằng model production."""
        if not class_labels:
            raise ValueError('Mô hình chưa có danh sách class để dự đoán.')

        model_path = cls._resolve_model_path(cnn_model)
        if cls._should_simulate(model_path):
            return cls._predict_simulation(image_path, cnn_model, class_labels, top_k)

        return cls._predict_tensorflow(cnn_model, image_path, class_labels, model_path, top_k)

    @classmethod
    def _resolve_model_path(cls, cnn_model: CnnModel) -> Path:
        version = ModelVersionRepository.get_production(cnn_model.id)
        relative = version.model_path if version else cnn_model.model_file_path
        if not relative:
            raise ValueError('Mô hình chưa có file .h5 để phân loại.')
        return ModelLoaderService.resolve_absolute_path(relative)

    @classmethod
    def _should_simulate(cls, model_path: Path) -> bool:
        if settings.TRAINING_SIMULATION_MODE:
            return True
        if not check_tensorflow()[0]:
            return True
        if not model_path.is_file():
            return True
        try:
            content = model_path.read_text(encoding='utf-8')
            if content.strip() == cls.SIMULATION_MARKER:
                return True
        except (OSError, UnicodeDecodeError):
            pass
        return False

    @classmethod
    def _predict_tensorflow(
        cls,
        cnn_model: CnnModel,
        image_path: Path,
        class_labels: list[str],
        model_path: Path,
        top_k: int,
    ) -> InferenceResult:
        started = time.time()
        batch, meta = InferenceImagePreprocessor.preprocess(
            image_path,
            cnn_model.input_width,
            cnn_model.input_height,
        )

        from tensorflow.keras.models import load_model
        import numpy as np

        model = load_model(str(model_path))
        probs = model.predict(batch, verbose=0)[0]
        scores = cls._build_scores(class_labels, probs, top_k)
        elapsed = round((time.time() - started) * 1000, 2)

        top = scores[0]
        return InferenceResult(
            predicted_class=top.class_name,
            confidence_score=top.probability,
            scores=scores,
            preprocess_meta=meta,
            inference_time_ms=elapsed,
            is_simulation=False,
        )

    @classmethod
    def _predict_simulation(
        cls,
        image_path: Path,
        cnn_model: CnnModel,
        class_labels: list[str],
        top_k: int,
    ) -> InferenceResult:
        """Mô phỏng softmax — deterministic theo hash ảnh."""
        started = time.time()
        batch, meta = InferenceImagePreprocessor.preprocess(
            image_path,
            cnn_model.input_width,
            cnn_model.input_height,
        )
        del batch

        digest = hashlib.md5(image_path.read_bytes()).hexdigest()
        seed = int(digest[:8], 16)
        raw = [(seed >> (i * 4)) % 1000 + 1 for i in range(len(class_labels))]
        total = float(sum(raw))
        probs = [value / total for value in raw]
        scores = cls._build_scores(class_labels, probs, top_k)
        elapsed = round((time.time() - started) * 1000, 2)

        top = scores[0]
        return InferenceResult(
            predicted_class=top.class_name,
            confidence_score=top.probability,
            scores=scores,
            preprocess_meta=meta,
            inference_time_ms=elapsed,
            is_simulation=True,
        )

    @staticmethod
    def _build_scores(class_labels: list[str], probabilities, top_k: int) -> list[ClassScore]:
        import numpy as np

        pairs = []
        for idx, label in enumerate(class_labels):
            prob = float(probabilities[idx]) if idx < len(probabilities) else 0.0
            pairs.append(ClassScore(class_name=label, probability=prob))

        pairs.sort(key=lambda item: item.probability, reverse=True)
        limit = min(top_k, len(pairs)) if top_k > 0 else len(pairs)
        return pairs[:limit]
