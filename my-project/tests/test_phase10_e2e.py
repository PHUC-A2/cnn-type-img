"""Phase 10 — End-to-end testing: dataset → train → predict → history + các flow HTTP."""

import io
import zipfile
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.datasets.models import Dataset
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from apps.predictions.models import Prediction, PredictionProbability
from apps.predictions.services.prediction_service import PredictionService
from apps.training.models import TrainingHistory, TrainingJob
from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
from apps.training.services.training_service import TrainingService
from core.enums.training_status import TrainingStatus
from core.enums.user_role import UserRole


def _make_image_bytes(color='blue', size=(48, 48)) -> bytes:
    """Tạo ảnh PNG hợp lệ cho test."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', size, color=color).save(buf, format='PNG')
    return buf.getvalue()


def _make_dataset_zip(classes=None, images_per_class=2) -> bytes:
    """Tạo ZIP dataset: mỗi class là một thư mục chứa ảnh."""
    classes = classes or ['cat', 'dog']
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for cls_name in classes:
            for idx in range(images_per_class):
                zf.writestr(f'{cls_name}/img_{idx}.png', _make_image_bytes())
    buf.seek(0)
    return buf.read()


def _run_simulation_training(user, dataset_id, model_name='E2E Model', epochs=2):
    """Khởi tạo job huấn luyện và chạy simulation đồng bộ."""
    with patch('apps.training.services.training_service.TrainingService.launch_background'):
        result = TrainingService.start_training(
            user=user,
            dataset_id=dataset_id,
            model_name=model_name,
            description='E2E test',
            input_width=64,
            input_height=64,
            epochs=epochs,
            batch_size=4,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
        )
    assert result.success, result.message
    SimulationTrainerService.run(result.job.id)
    return result.job


class EndToEndCnnPipelineTest(TransactionTestCase):
    """E2E service layer: upload dataset → train → predict → kiểm tra history."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='e2euser',
            email='e2e@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_full_pipeline_dataset_train_predict_history(self):
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='E2E Animals',
            zip_file=SimpleUploadedFile('e2e.zip', zip_content, content_type='application/zip'),
        )
        self.assertTrue(ds_result.success, ds_result.message)
        dataset = ds_result.dataset
        self.assertEqual(dataset.total_classes, 2)
        self.assertEqual(dataset.total_images, 4)

        job = _run_simulation_training(self.user, dataset.id)
        job.refresh_from_db()
        self.assertEqual(job.training_status, TrainingStatus.COMPLETED.value)
        self.assertEqual(TrainingHistory.objects.filter(training_job=job).count(), 2)
        self.assertTrue(job.model.model_file_path)

        image = SimpleUploadedFile('predict.png', _make_image_bytes(), content_type='image/png')
        pred_result = PredictionService.run_prediction(
            user=self.user,
            model_id=job.model_id,
            image_file=image,
            top_k=2,
        )
        self.assertTrue(pred_result.success, pred_result.message)
        prediction = pred_result.prediction
        self.assertEqual(Prediction.objects.filter(predicted_by=self.user).count(), 1)
        self.assertEqual(PredictionProbability.objects.filter(prediction=prediction).count(), 2)
        self.assertTrue(prediction.predicted_class)
        self.assertGreater(prediction.confidence_score, 0)


class AuthFlowHttpTest(TestCase):
    """Flow HTTP: đăng ký → đăng nhập → dashboard → đăng xuất."""

    def setUp(self):
        self.client = Client()

    def test_register_login_dashboard_logout(self):
        response = self.client.post(reverse('authentication:register'), {
            'username': 'newe2e',
            'email': 'newe2e@test.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'E2E User',
        })
        self.assertRedirects(response, reverse('authentication:login'))
        self.assertTrue(User.objects.filter(username='newe2e').exists())

        response = self.client.post(reverse('authentication:login'), {
            'username': 'newe2e',
            'password': 'password123',
        })
        self.assertRedirects(response, reverse('authentication:dashboard'))

        response = self.client.get(reverse('authentication:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bảng điều khiển')

        response = self.client.get(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('authentication:login'))


class DatasetUploadFlowHttpTest(TestCase):
    """Flow HTTP: upload dataset ZIP qua form."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='dsflow',
            email='dsflow@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'dsflow',
            'password': 'pass123',
        })

    def test_dataset_upload_via_form(self):
        zip_content = _make_dataset_zip()
        response = self.client.post(reverse('datasets:upload'), {
            'dataset_name': 'HTTP Dataset',
            'description': 'Upload qua form',
            'zip_file': SimpleUploadedFile('http.zip', zip_content, content_type='application/zip'),
        })
        dataset = Dataset.objects.filter(dataset_name='HTTP Dataset').first()
        self.assertIsNotNone(dataset)
        self.assertRedirects(response, reverse('datasets:detail', kwargs={'dataset_id': dataset.id}))

        response = self.client.get(reverse('datasets:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'HTTP Dataset')


class TrainingFlowHttpTest(TransactionTestCase):
    """Flow HTTP: bắt đầu huấn luyện CNN qua form."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='trainflow',
            email='trainflow@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'trainflow',
            'password': 'pass123',
        })
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Train Flow DS',
            zip_file=SimpleUploadedFile('train.zip', zip_content, content_type='application/zip'),
        )
        self.dataset = ds_result.dataset

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_training_start_via_form(self):
        with patch('apps.training.services.training_service.TrainingService.launch_background'):
            response = self.client.post(reverse('training:list'), {
                'model_name': 'HTTP CNN Model',
                'dataset_id': str(self.dataset.id),
                'description': 'Test training',
                'input_width': 64,
                'input_height': 64,
                'epochs': 2,
                'batch_size': 4,
                'learning_rate': '0.001',
                'optimizer': 'adam',
                'loss_function': 'categorical_crossentropy',
            })

        job = TrainingJob.objects.filter(model__model_name='HTTP CNN Model').first()
        self.assertIsNotNone(job)
        SimulationTrainerService.run(job.id)
        job.refresh_from_db()
        self.assertEqual(job.training_status, TrainingStatus.COMPLETED.value)
        self.assertRedirects(response, reverse('training:detail', kwargs={'job_id': job.id}))

        response = self.client.get(reverse('training:detail', kwargs={'job_id': job.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'HTTP CNN Model')


class PredictionFlowHttpTest(TransactionTestCase):
    """Flow HTTP: phân loại ảnh sau khi huấn luyện."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='predictflow',
            email='predictflow@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'predictflow',
            'password': 'pass123',
        })
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Predict Flow DS',
            zip_file=SimpleUploadedFile('pred.zip', zip_content, content_type='application/zip'),
        )
        self.job = _run_simulation_training(self.user, ds_result.dataset.id, 'Predict Flow Model')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_predict_via_form(self):
        image = SimpleUploadedFile('test.png', _make_image_bytes(), content_type='image/png')
        response = self.client.post(reverse('predictions:predict'), {
            'model_id': str(self.job.model_id),
            'image': image,
            'top_k': 2,
        })
        prediction = Prediction.objects.filter(predicted_by=self.user).first()
        self.assertIsNotNone(prediction)
        self.assertRedirects(
            response,
            reverse('predictions:result', kwargs={'prediction_id': prediction.id}),
        )

        response = self.client.get(
            reverse('predictions:result', kwargs={'prediction_id': prediction.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, prediction.predicted_class)


class HistoryFlowHttpTest(TransactionTestCase):
    """Flow HTTP: xem lịch sử phân loại sau predict."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='histflow',
            email='histflow@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'histflow',
            'password': 'pass123',
        })
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='History Flow DS',
            zip_file=SimpleUploadedFile('hist.zip', zip_content, content_type='application/zip'),
        )
        job = _run_simulation_training(self.user, ds_result.dataset.id, 'History Model')
        image = SimpleUploadedFile('hist.png', _make_image_bytes(), content_type='image/png')
        PredictionService.run_prediction(
            user=self.user,
            model_id=job.model_id,
            image_file=image,
            top_k=2,
        )

    def test_history_list_and_detail_modal(self):
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lịch sử phân loại')

        prediction = Prediction.objects.filter(predicted_by=self.user).first()
        response = self.client.get(
            reverse('predictions:history_detail', kwargs={'prediction_id': prediction.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, prediction.predicted_class)


class AdminPanelFlowHttpTest(TestCase):
    """Flow HTTP: admin đăng nhập và truy cập các trang quản trị."""

    def setUp(self):
        self.client = Client()
        self.admin = UserRepository.create_user(
            username='e2eadmin',
            email='e2eadmin@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'e2eadmin',
            'password': 'admin123',
        })

    def test_admin_panel_full_navigation(self):
        pages = [
            ('monitoring:dashboard', 'Bảng quản trị'),
            ('monitoring:users_list', 'Quản lý người dùng'),
            ('monitoring:datasets_list', 'Quản lý bộ dữ liệu'),
            ('monitoring:models_list', 'Quản lý mô hình'),
            ('monitoring:training_list', 'Job huấn luyện'),
            ('monitoring:predictions_list', 'Lịch sử phân loại'),
            ('monitoring:logs', 'Log hệ thống'),
        ]
        for url_name, expected_text in pages:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, url_name)
            self.assertContains(response, expected_text)
