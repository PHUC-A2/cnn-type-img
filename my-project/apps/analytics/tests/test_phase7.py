"""Test Phase 7 — Analytics Dashboard."""

import io
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.analytics.services.analytics_dashboard_service import AnalyticsDashboardService
from apps.analytics.services.chart_image_service import ChartImageService
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.models_ai.models import CnnModel
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from apps.predictions.services.prediction_service import PredictionService
from apps.training.models import ModelMetrics
from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
from apps.training.services.training_service import TrainingService
from core.enums.user_role import UserRole


def _make_image_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (32, 32), color='blue').save(buf, format='PNG')
    return buf.getvalue()


def _make_dataset_zip() -> bytes:
    import zipfile

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for cls_name in ('cat', 'dog'):
            for idx in range(2):
                zf.writestr(f'{cls_name}/img_{idx}.png', _make_image_bytes())
    buf.seek(0)
    return buf.read()


class AnalyticsDashboardTest(TransactionTestCase):
    """Test trang /analytics/ — TransactionTestCase vì trainer đóng/mở DB."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='analyticsuser',
            email='analytics@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self._prepare_training_and_prediction()

    def _prepare_training_and_prediction(self):
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Analytics DS',
            zip_file=SimpleUploadedFile('analytics.zip', zip_content, content_type='application/zip'),
        )
        self.dataset = ds_result.dataset

        with patch('apps.training.services.training_service.TrainingService.launch_background'):
            start = TrainingService.start_training(
                user=self.user,
                dataset_id=self.dataset.id,
                model_name='Analytics Model',
                description='',
                input_width=64,
                input_height=64,
                epochs=2,
                batch_size=4,
                learning_rate=0.001,
                optimizer='adam',
                loss_function='categorical_crossentropy',
            )
        self.assertTrue(start.success)
        SimulationTrainerService.run(start.job.id)
        self.job = start.job

        model = CnnModel.objects.get(id=self.job.model_id)
        image = SimpleUploadedFile('pic.png', _make_image_bytes(), content_type='image/png')
        PredictionService.run_prediction(self.user, model.id, image, top_k=2)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_analytics_requires_login(self):
        response = self.client.get(reverse('analytics:index'))
        self.assertRedirects(response, reverse('authentication:login'))

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_analytics_page_renders(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'analyticsuser',
            'password': 'pass123',
        })
        response = self.client.get(reverse('analytics:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phân tích AI')
        self.assertContains(response, 'So sánh mô hình')
        self.assertContains(response, 'Confusion Matrix')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_analytics_shows_training_charts_for_job(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'analyticsuser',
            'password': 'pass123',
        })
        response = self.client.get(reverse('analytics:index'), {'job_id': self.job.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'analyticsAccuracyChart')
        self.assertContains(response, 'Analytics Model')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_dashboard_service_builds_confusion_matrix(self):
        dashboard = AnalyticsDashboardService.build_dashboard(self.user, job_id=self.job.id)
        self.assertEqual(dashboard.summary.completed_jobs, 1)
        self.assertEqual(dashboard.summary.total_predictions, 1)
        self.assertTrue(dashboard.confusion.matrix)
        self.assertEqual(len(dashboard.confusion.labels), 2)
        self.assertEqual(len(dashboard.training_chart.labels), 2)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_simulation_training_saves_confusion_matrix(self):
        metrics = ModelMetrics.objects.filter(training_job=self.job).first()
        self.assertIsNotNone(metrics)
        self.assertIsNotNone(metrics.confusion_matrix_json)
        self.assertEqual(len(metrics.class_labels_json), 2)

class ChartImageServiceTest(TestCase):
    """Test render ảnh confusion matrix."""

    def test_chart_image_service_renders_png(self):
        matrix = [[10, 2], [1, 12]]
        labels = ['cat', 'dog']
        encoded = ChartImageService.render_confusion_matrix(matrix, labels)
        self.assertIsNotNone(encoded)
        self.assertTrue(len(encoded) > 100)
