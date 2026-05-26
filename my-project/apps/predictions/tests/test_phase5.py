"""Test Phase 5 — Image Prediction."""

import io
import zipfile
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from apps.models_ai.models import CnnModel
from apps.models_ai.services.model_version_service import ModelVersionService
from apps.predictions.models import Prediction, PredictionProbability
from apps.predictions.services.prediction_service import PredictionService
from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
from apps.training.services.training_service import TrainingService
from core.enums.training_status import TrainingStatus
from core.enums.user_role import UserRole


def _make_image_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (48, 48), color='blue').save(buf, format='PNG')
    return buf.getvalue()


def _make_dataset_zip(classes=None, images_per_class=2) -> bytes:
    classes = classes or ['cat', 'dog']
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for cls_name in classes:
            for idx in range(images_per_class):
                zf.writestr(f'{cls_name}/img_{idx}.png', _make_image_bytes())
    buf.seek(0)
    return buf.read()


class PredictionFlowTest(TransactionTestCase):
    """E2E predict với model mô phỏng."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='predictuser',
            email='predict@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Predict DS',
            zip_file=SimpleUploadedFile('predict.zip', zip_content, content_type='application/zip'),
        )
        self.assertTrue(ds_result.success, ds_result.message)
        self.dataset = ds_result.dataset

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_full_predict_flow(self):
        with patch('apps.training.services.training_service.TrainingService.launch_background'):
            start = TrainingService.start_training(
                user=self.user,
                dataset_id=self.dataset.id,
                model_name='Predict Model',
                description='',
                input_width=128,
                input_height=128,
                epochs=2,
                batch_size=8,
                learning_rate=0.001,
                optimizer='adam',
                loss_function='categorical_crossentropy',
            )
        self.assertTrue(start.success)
        SimulationTrainerService.run(start.job.id)

        image = SimpleUploadedFile('test.png', _make_image_bytes(), content_type='image/png')
        result = PredictionService.run_prediction(
            user=self.user,
            model_id=start.job.model_id,
            image_file=image,
            top_k=2,
        )
        self.assertTrue(result.success, result.message)
        self.assertEqual(Prediction.objects.count(), 1)
        self.assertEqual(PredictionProbability.objects.filter(prediction=result.prediction).count(), 2)
        self.assertTrue(result.prediction.is_simulation)


class PredictionViewTest(TestCase):
    """Test views /predict/ và /predict/result/."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='predictview',
            email='pv@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'predictview',
            'password': 'pass123',
        })

        self.model = CnnModel.objects.create(
            model_name='View Predict Model',
            model_slug='view-predict',
            input_width=128,
            input_height=128,
            created_by=self.user,
            model_file_path='view-predict/job_1.h5',
        )
        model_dir = settings.MODEL_ROOT / 'view-predict'
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / 'job_1.h5').write_text('SIMULATED_MODEL_PLACEHOLDER', encoding='utf-8')

        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='View DS',
            zip_file=SimpleUploadedFile('vds.zip', zip_content, content_type='application/zip'),
        )
        self.dataset = ds_result.dataset

        from apps.training.models import TrainingJob
        self.job = TrainingJob.objects.create(
            model=self.model,
            dataset=self.dataset,
            trained_by=self.user,
            training_status=TrainingStatus.COMPLETED.value,
            epochs=3,
            batch_size=8,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
            validation_accuracy=0.88,
        )
        ModelVersionService.create_from_completed_job(self.job)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_predict_page(self):
        response = self.client.get(reverse('predictions:predict'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phân loại ảnh')
        self.assertContains(response, 'Hướng dẫn phân loại ảnh')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_predict_post_redirects_to_result(self):
        response = self.client.post(reverse('predictions:predict'), {
            'model_id': str(self.model.id),
            'top_k': '2',
            'image': SimpleUploadedFile('pic.png', _make_image_bytes(), content_type='image/png'),
        })
        prediction = Prediction.objects.first()
        self.assertIsNotNone(prediction)
        self.assertRedirects(response, reverse('predictions:result', args=[prediction.id]))

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_result_page(self):
        image = SimpleUploadedFile('pic.png', _make_image_bytes(), content_type='image/png')
        run = PredictionService.run_prediction(self.user, self.model.id, image, top_k=2)
        response = self.client.get(reverse('predictions:result', args=[run.prediction.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, run.prediction.predicted_class)
        self.assertContains(response, 'probabilityChart')
