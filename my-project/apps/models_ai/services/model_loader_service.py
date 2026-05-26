"""Load và tải xuống file model .h5."""

from pathlib import Path

from django.conf import settings

from apps.models_ai.models import CnnModel, ModelVersion


class ModelLoaderService:
    """Đọc file model từ trained_models/ và phục vụ download."""

    @staticmethod
    def resolve_absolute_path(relative_path: str) -> Path:
        """Chuyển path DB thành đường dẫn tuyệt đối trên disk."""
        return Path(settings.MODEL_ROOT) / relative_path

    @staticmethod
    def file_exists(relative_path: str) -> bool:
        """Kiểm tra file model có tồn tại hay không."""
        if not relative_path:
            return False
        path = ModelLoaderService.resolve_absolute_path(relative_path)
        return path.is_file() and path.stat().st_size > 0

    @staticmethod
    def load_keras_model(relative_path: str):
        """Load model Keras từ file .h5 — dùng cho inference Phase 5."""
        path = ModelLoaderService.resolve_absolute_path(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f'Không tìm thấy file model: {relative_path}')
        from tensorflow.keras.models import load_model
        return load_model(str(path))

    @staticmethod
    def build_download_filename(model: CnnModel, version: ModelVersion) -> str:
        """Tên file khi user tải xuống."""
        safe_slug = model.model_slug.replace('/', '-')
        return f'{safe_slug}_{version.version_number}.h5'

    @staticmethod
    def get_download_path(model: CnnModel, version: ModelVersion) -> Path:
        """Lấy path tuyệt đối để stream download."""
        path = ModelLoaderService.resolve_absolute_path(version.model_path)
        if not path.is_file():
            raise FileNotFoundError('File model không tồn tại trên hệ thống.')
        return path
