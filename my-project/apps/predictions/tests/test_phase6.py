"""Test Phase 6 — Prediction History."""

import io
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from apps.models_ai.models import CnnModel
from apps.models_ai.services.model_version_service import ModelVersionService
from apps.predictions.models import Prediction
from apps.predictions.services.prediction_service import PredictionService
from apps.training.models import TrainingJob
from core.enums.training_status import TrainingStatus
from core.enums.user_role import UserRole


def _make_image_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (32, 32), color='green').save(buf, format='PNG')
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


class HistoryViewTest(TestCase):
    """Test trang lịch sử phân loại."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='historyuser',
            email='history@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.other = UserRepository.create_user(
            username='otherhist',
            email='otherhist@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self._setup_model_and_prediction(self.user)
        self._setup_model_and_prediction(self.other)

    def _setup_model_and_prediction(self, user):
        zip_content = _make_dataset_zip()
        ds_result = DatasetUploadService.upload_from_zip(
            user=user,
            dataset_name=f'DS {user.username}',
            zip_file=SimpleUploadedFile('ds.zip', zip_content, content_type='application/zip'),
        )
        model = CnnModel.objects.create(
            model_name=f'Model {user.username}',
            model_slug=f'model-{user.username}',
            input_width=128,
            input_height=128,
            created_by=user,
            model_file_path=f'model-{user.username}/job_1.h5',
        )
        model_dir = settings.MODEL_ROOT / f'model-{user.username}'
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / 'job_1.h5').write_text('SIMULATED_MODEL_PLACEHOLDER', encoding='utf-8')

        job = TrainingJob.objects.create(
            model=model,
            dataset=ds_result.dataset,
            trained_by=user,
            training_status=TrainingStatus.COMPLETED.value,
            epochs=2,
            batch_size=8,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
        )
        ModelVersionService.create_from_completed_job(job)

        image = SimpleUploadedFile('pic.png', _make_image_bytes(), content_type='image/png')
        PredictionService.run_prediction(user, model.id, image, top_k=2)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_requires_login(self):
        response = self.client.get(reverse('predictions:history'))
        self.assertRedirects(response, reverse('authentication:login'))

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_page_lists_own_records(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lịch sử phân loại')
        self.assertContains(response, 'Model historyuser')
        self.assertNotContains(response, 'Model otherhist')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_filter_by_model(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        model = CnnModel.objects.get(model_slug='model-historyuser')
        response = self.client.get(reverse('predictions:history'), {'model_id': model.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Model historyuser')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_detail_partial(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        prediction = Prediction.objects.filter(predicted_by=self.user).first()
        response = self.client.get(reverse('predictions:history_detail', args=[prediction.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Chi tiết phân loại')
        self.assertContains(response, prediction.predicted_class)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_detail_forbidden_for_other_user(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        other_prediction = Prediction.objects.filter(predicted_by=self.other).first()
        response = self.client.get(reverse('predictions:history_detail', args=[other_prediction.id]))
        self.assertEqual(response.status_code, 403)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_search_by_class(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        prediction = Prediction.objects.filter(predicted_by=self.user).first()
        response = self.client.get(reverse('predictions:history'), {'q': prediction.predicted_class[:3]})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, prediction.predicted_class)

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_history_pagination(self):
        model = CnnModel.objects.get(model_slug='model-historyuser')
        image = SimpleUploadedFile('pic.png', _make_image_bytes(), content_type='image/png')
        for _ in range(10):
            PredictionService.run_prediction(self.user, model.id, image, top_k=2)

        self.client.post(reverse('authentication:login'), {
            'username': 'historyuser',
            'password': 'pass123',
        })
        page1 = self.client.get(reverse('predictions:history'))
        self.assertEqual(page1.status_code, 200)
        self.assertContains(page1, 'Trang 1 / 2')

        page2 = self.client.get(reverse('predictions:history'), {'page': 2})
        self.assertEqual(page2.status_code, 200)
        self.assertContains(page2, 'Trang 2 / 2')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    def test_admin_sees_all_users(self):
        admin = UserRepository.create_user(
            username='adminhist',
            email='adminhist@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'adminhist',
            'password': 'admin123',
        })
        response = self.client.get(reverse('predictions:history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Model historyuser')
        self.assertContains(response, 'Model otherhist')
        self.assertContains(response, 'Người dùng')
