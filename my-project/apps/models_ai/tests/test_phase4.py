"""Test Phase 4 — Model Management."""

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
from apps.models_ai.models import CnnModel, ModelVersion
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.models_ai.services.model_loader_service import ModelLoaderService
from apps.models_ai.services.model_version_service import ModelVersionService
from apps.training.models import TrainingJob
from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
from apps.training.services.training_service import TrainingService
from core.enums.training_status import TrainingStatus
from core.enums.user_role import UserRole


def _make_image_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (1, 1), color='red').save(buf, format='PNG')
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


class ModelVersionServiceTest(TransactionTestCase):
    """Test service versioning — TransactionTestCase vì trainer đóng/mở DB connection."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='modeluser',
            email='model@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        zip_content = _make_dataset_zip()
        result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Model DS',
            zip_file=SimpleUploadedFile('ds.zip', zip_content, content_type='application/zip'),
        )
        self.assertTrue(result.success, result.message)
        self.dataset = result.dataset

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_training_creates_model_version(self):
        with patch('apps.training.services.training_service.TrainingService.launch_background'):
            start = TrainingService.start_training(
                user=self.user,
                dataset_id=self.dataset.id,
                model_name='Version Test',
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
        job = start.job

        SimulationTrainerService.run(job.id)

        job.refresh_from_db()
        self.assertEqual(job.training_status, TrainingStatus.COMPLETED.value)
        versions = ModelVersionRepository.list_by_model(job.model_id)
        self.assertEqual(versions.count(), 1)
        version = versions.first()
        self.assertTrue(version.is_production)
        self.assertTrue(ModelLoaderService.file_exists(version.model_path))


class ModelViewTest(TestCase):
    """Test views quản lý model."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='viewmodel',
            email='viewmodel@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        UserRepository.create_user(
            username='othermodel',
            email='other@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'viewmodel',
            'password': 'pass123',
        })

        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='View DS',
            zip_file=SimpleUploadedFile('view.zip', zip_content, content_type='application/zip'),
        )
        self.assertTrue(ds_result.success, ds_result.message)
        self.dataset = ds_result.dataset

        self.model = CnnModel.objects.create(
            model_name='Demo CNN',
            model_slug='demo-cnn',
            input_width=128,
            input_height=128,
            created_by=self.user,
            model_file_path='demo-cnn/job_1.h5',
            total_parameters=1000,
            model_size_mb=0.5,
        )
        model_dir = settings.MODEL_ROOT / 'demo-cnn'
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / 'job_1.h5').write_text('demo model', encoding='utf-8')

        self.job = TrainingJob.objects.create(
            model=self.model,
            dataset=self.dataset,
            trained_by=self.user,
            training_status=TrainingStatus.COMPLETED.value,
            epochs=5,
            batch_size=16,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
            validation_accuracy=0.91,
        )
        ModelVersionService.create_from_completed_job(self.job)

    def test_list_page(self):
        response = self.client.get(reverse('models_ai:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mô hình CNN')
        self.assertContains(response, 'Demo CNN')

    def test_detail_page(self):
        response = self.client.get(reverse('models_ai:detail', args=[self.model.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phiên bản mô hình')
        self.assertContains(response, 'Production')

    def test_download_model(self):
        response = self.client.get(reverse('models_ai:download', args=[self.model.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response.get('Content-Disposition', ''))

    def test_set_production(self):
        (settings.MODEL_ROOT / 'demo-cnn' / 'job_2.h5').write_text('v2', encoding='utf-8')
        version2 = ModelVersionRepository.create(
            model=self.model,
            version_name='v2',
            version_number='1.0.2',
            model_path='demo-cnn/job_2.h5',
            accuracy_score=0.95,
            is_production=False,
        )
        response = self.client.post(
            reverse('models_ai:set_production', args=[self.model.id, version2.id]),
        )
        self.assertRedirects(response, reverse('models_ai:detail', args=[self.model.id]))
        version2.refresh_from_db()
        self.assertTrue(version2.is_production)
        v1 = ModelVersion.objects.get(model=self.model, version_number='1.0.1')
        self.assertFalse(v1.is_production)

    def test_other_user_forbidden_detail(self):
        self.client.get(reverse('authentication:logout'))
        self.client.post(reverse('authentication:login'), {
            'username': 'othermodel',
            'password': 'pass123',
        })
        response = self.client.get(reverse('models_ai:detail', args=[self.model.id]))
        self.assertRedirects(response, reverse('models_ai:list'))
