"""Huấn luyện CNN bằng TensorFlow/Keras."""

import time
from pathlib import Path

from django.utils import timezone

from apps.models_ai.services.model_version_service import ModelVersionService
from apps.training.models import TrainingHistory, TrainingJob
from apps.training.repositories.training_job_repository import TrainingJobRepository
from apps.training.services.cnn.architecture_builder import build_cnn_model
from apps.training.services.cnn.preprocessor import DatasetPreprocessorService
from apps.training.services.model_storage_service import ModelStorageService
from apps.training.services.training_metrics_service import TrainingMetricsService
from core.enums.training_status import TrainingStatus


class CnnTrainerService:
    """Chạy pipeline huấn luyện thật với Keras."""

    @classmethod
    def run(cls, job_id: int) -> None:
        from django.db import close_old_connections

        close_old_connections()
        job = TrainingJobRepository.get_by_id(job_id)
        if not job:
            return

        data_root = None
        started = time.time()
        try:
            cls._update_job(job, TrainingStatus.PREPARING, 'Đang chuẩn bị dữ liệu...')
            prep = DatasetPreprocessorService.build_training_dirs(job.dataset, job.id)
            data_root = prep.root
            if prep.skipped:
                cls._update_job(
                    job,
                    TrainingStatus.PREPARING,
                    f'Đã lọc {len(prep.skipped)} ảnh lỗi, dùng {prep.copied} ảnh hợp lệ...',
                )

            cls._update_job(job, TrainingStatus.TRAINING, 'Đang huấn luyện mô hình...')
            eval_data = cls._train_keras(job, data_root)

            cls._update_job(job, TrainingStatus.VALIDATING, 'Đang tính metrics...')
            cls._save_metrics(job, eval_data)

            ModelVersionService.on_training_completed(job.id)

            job.execution_time = round(time.time() - started, 2)
            job.finished_at = timezone.now()
            cls._update_job(job, TrainingStatus.COMPLETED, 'Huấn luyện hoàn thành.')
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.info(
                'training',
                f'Huấn luyện hoàn thành job #{job.id} — {job.model.model_name}',
                context={
                    'job_id': job.id,
                    'execution_time_s': job.execution_time,
                    'validation_accuracy': job.validation_accuracy,
                },
            )
        except Exception as exc:
            job.execution_time = round(time.time() - started, 2)
            job.finished_at = timezone.now()
            cls._update_job(job, TrainingStatus.FAILED, cls._format_training_error(exc))
            from apps.monitoring.services.system_log_service import SystemLogService
            SystemLogService.error(
                'training',
                f'Huấn luyện thất bại job #{job.id}',
                exc=exc,
                context={'job_id': job.id},
            )
        finally:
            DatasetPreprocessorService.cleanup(data_root)
            close_old_connections()

    @classmethod
    def _train_keras(cls, job: TrainingJob, data_root: Path):
        """Huấn luyện Keras — trả về tuple (y_true, y_pred, labels) để đánh giá."""
        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
        from tensorflow.keras.optimizers import Adam, RMSprop, SGD
        from tensorflow.keras.preprocessing.image import ImageDataGenerator

        tf.keras.utils.set_random_seed(42)

        input_shape = (job.model.input_height, job.model.input_width, job.model.channels)
        target_size = (job.model.input_width, job.model.input_height)

        train_datagen = ImageDataGenerator(
            rescale=1.0 / 255,
            rotation_range=20,
            width_shift_range=0.15,
            height_shift_range=0.15,
            horizontal_flip=True,
        )
        val_datagen = ImageDataGenerator(rescale=1.0 / 255)

        train_gen = train_datagen.flow_from_directory(
            data_root / 'train',
            target_size=target_size,
            batch_size=job.batch_size,
            class_mode='categorical',
            shuffle=True,
        )
        val_gen = val_datagen.flow_from_directory(
            data_root / 'val',
            target_size=target_size,
            batch_size=job.batch_size,
            class_mode='categorical',
            shuffle=False,
        )

        num_classes = train_gen.num_classes
        model = build_cnn_model(input_shape, num_classes)
        optimizer = cls._get_optimizer(job.optimizer, job.learning_rate)
        model.compile(optimizer=optimizer, loss=job.loss_function, metrics=['accuracy'])

        model_path = ModelStorageService.build_model_path(job.model.model_slug, job.id)
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True),
            ModelCheckpoint(str(model_path), monitor='val_loss', save_best_only=True),
            create_epoch_logger(job.id),
        ]

        history = model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=job.epochs,
            callbacks=callbacks,
            verbose=0,
        )

        if not model_path.exists():
            model.save(str(model_path))

        cls._finalize_model(job, model, model_path, history)

        try:
            import numpy as np

            y_pred_probs = model.predict(val_gen, verbose=0)
            y_pred = np.argmax(y_pred_probs, axis=1)
            val_gen.reset()
            y_true = val_gen.classes[: len(y_pred)]
            class_labels = sorted(
                train_gen.class_indices.keys(),
                key=lambda name: train_gen.class_indices[name],
            )
            return y_true, y_pred, class_labels
        except Exception:
            return None

    @staticmethod
    def _get_optimizer(name: str, lr: float):
        from tensorflow.keras.optimizers import Adam, RMSprop, SGD

        mapping = {
            'adam': Adam(learning_rate=lr),
            'sgd': SGD(learning_rate=lr),
            'rmsprop': RMSprop(learning_rate=lr),
        }
        return mapping.get(name, Adam(learning_rate=lr))

    @classmethod
    def _finalize_model(cls, job, model, model_path, history) -> None:
        cnn = job.model
        cnn.total_parameters = int(model.count_params())
        cnn.model_file_path = ModelStorageService.relative_model_path(cnn.model_slug, job.id)
        cnn.model_size_mb = ModelStorageService.get_file_size_mb(model_path)
        cnn.save()

        if history.history:
            job.train_accuracy = float(history.history['accuracy'][-1])
            job.validation_accuracy = float(history.history['val_accuracy'][-1])
            job.train_loss = float(history.history['loss'][-1])
            job.validation_loss = float(history.history['val_loss'][-1])
            TrainingJobRepository.save(job)

    @classmethod
    def _save_metrics(cls, job: TrainingJob, eval_data=None) -> None:
        """Lưu metrics — ưu tiên sklearn nếu có dữ liệu validation."""
        if eval_data:
            y_true, y_pred, class_labels = eval_data
            TrainingMetricsService.save_from_predictions(job, y_true, y_pred, class_labels)
            return
        TrainingMetricsService.save_fallback(job)

    @staticmethod
    def _format_training_error(exc: Exception) -> str:
        """Rút gọn lỗi TensorFlow/Pillow thành thông báo tiếng Việt."""
        msg = str(exc)
        if 'UnidentifiedImageError' in msg or 'cannot identify image file' in msg:
            return (
                'Huấn luyện thất bại: bộ dữ liệu có ảnh lỗi hoặc file 0 byte. '
                'Vui lòng kiểm tra dataset và tải lại ZIP.'
            )
        if len(msg) > 300:
            return f'Huấn luyện thất bại: {msg[:300]}...'
        return f'Huấn luyện thất bại: {msg}'

    @staticmethod
    def _update_job(job: TrainingJob, status: TrainingStatus, message: str) -> None:
        job.training_status = status.value
        job.status_message = message
        if status == TrainingStatus.TRAINING and not job.started_at:
            job.started_at = timezone.now()
        TrainingJobRepository.save(job)


def create_epoch_logger(job_id: int):
    """Factory callback ghi epoch vào DB."""
    from tensorflow.keras.callbacks import Callback

    class EpochLoggerCallback(Callback):
        def on_epoch_end(self, epoch, logs=None):
            from django.db import close_old_connections
            close_old_connections()
            logs = logs or {}
            TrainingHistory.objects.create(
                training_job_id=job_id,
                epoch_number=epoch + 1,
                train_accuracy=float(logs.get('accuracy', 0)),
                validation_accuracy=float(logs.get('val_accuracy', 0)),
                train_loss=float(logs.get('loss', 0)),
                validation_loss=float(logs.get('val_loss', 0)),
            )
            job = TrainingJob.objects.get(id=job_id)
            job.train_accuracy = float(logs.get('accuracy', 0))
            job.validation_accuracy = float(logs.get('val_accuracy', 0))
            job.train_loss = float(logs.get('loss', 0))
            job.validation_loss = float(logs.get('val_loss', 0))
            job.status_message = f'Epoch {epoch + 1}/{job.epochs} — đang huấn luyện...'
            job.save(update_fields=[
                'train_accuracy', 'validation_accuracy', 'train_loss',
                'validation_loss', 'status_message',
            ])

    return EpochLoggerCallback()
