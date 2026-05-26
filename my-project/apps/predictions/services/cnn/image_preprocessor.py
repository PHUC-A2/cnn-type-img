"""Tiền xử lý ảnh trước inference CNN — resize, RGB, chuẩn hóa."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PreprocessMeta:
    """Metadata ảnh sau tiền xử lý."""

    original_width: int
    original_height: int
    target_width: int
    target_height: int
    channels: int
    normalize_scale: float


class InferenceImagePreprocessor:
    """Pipeline resize + normalize cho Keras predict."""

    NORMALIZE_SCALE = 1.0 / 255.0

    @classmethod
    def preprocess(cls, image_path: Path, target_width: int, target_height: int):
        """
        Trả về (batch_tensor, PreprocessMeta).
        batch_tensor shape: (1, height, width, channels)
        """
        from PIL import Image
        import numpy as np

        with Image.open(image_path) as img:
            img = img.convert('RGB')
            original_width, original_height = img.size
            resized = img.resize((target_width, target_height))
            array = np.asarray(resized, dtype='float32') * cls.NORMALIZE_SCALE
            batch = np.expand_dims(array, axis=0)

        meta = PreprocessMeta(
            original_width=original_width,
            original_height=original_height,
            target_width=target_width,
            target_height=target_height,
            channels=3,
            normalize_scale=cls.NORMALIZE_SCALE,
        )
        return batch, meta
