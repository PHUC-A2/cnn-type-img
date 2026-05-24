"""Test Phase 3 — CNN Training."""

import time
from pathlib import Path
from unittest.mock import patch

from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.datasets.models import Dataset, DatasetClass, DatasetImage
from apps.training.models import TrainingHistory, TrainingJob
from apps.training.services.training_service import TrainingService
from core.enums.training_status import TrainingStatus
from core.enums.user_role import UserRole


class TrainingServiceTest(TransactionTestCase):
    """Test khởi tạo job huấn luyện — TransactionTestCase vì trainer đóng/mở DB connection."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='trainer',
            email='trainer@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.dataset = Dataset.objects.create(
            dataset_name='Train DS',
            dataset_slug='train-ds',
            dataset_path='datasets/train-ds/',
            total_images=4,
            total_classes=2,
            created_by=self.user,
        )
        cat = DatasetClass.objects.create(dataset=self.dataset, class_name='cat', class_slug='cat', total_images=2)
        dog = DatasetClass.objects.create(dataset=self.dataset, class_name='dog', class_slug='dog', total_images=2)
        for idx, cls in enumerate([cat, cat, dog, dog]):
            DatasetImage.objects.create(
                dataset=self.dataset,
                dataset_class=cls,
                image_name=f'{idx}.png',
                image_url=f'/media/datasets/train-ds/{cls.class_slug}/{idx}.png',
                is_train=idx < 2,
            )

    @override_settings(TRAINING_SIMULATION_MODE=True)
    @patch('apps.training.services.training_service.TrainingService.launch_background')
    def test_start_training_creates_job(self, mock_launch):
        result = TrainingService.start_training(
            user=self.user,
            dataset_id=self.dataset.id,
            model_name='CNN Test',
            description='',
            input_width=128,
            input_height=128,
            epochs=3,
            batch_size=8,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
        )
        self.assertTrue(result.success, result.message)
        self.assertIsNotNone(result.job)
        mock_launch.assert_called_once()

    @override_settings(TRAINING_SIMULATION_MODE=True)
    @patch('apps.training.services.training_service.TrainingService.launch_background')
    def test_simulation_training_completes(self, mock_launch):
        result = TrainingService.start_training(
            user=self.user,
            dataset_id=self.dataset.id,
            model_name='Sim CNN',
            description='',
            input_width=64,
            input_height=64,
            epochs=2,
            batch_size=4,
            learning_rate=0.001,
            optimizer='adam',
            loss_function='categorical_crossentropy',
        )
        self.assertTrue(result.success)
        mock_launch.assert_called_once()
        from apps.training.services.cnn.simulation_trainer import SimulationTrainerService
        SimulationTrainerService.run(result.job.id)

        job = TrainingJob.objects.get(id=result.job.id)
        self.assertEqual(job.training_status, TrainingStatus.COMPLETED.value)
        self.assertEqual(TrainingHistory.objects.filter(training_job=job).count(), 2)


class DatasetPreprocessorTest(TestCase):
    """Test lọc ảnh lỗi trước khi huấn luyện."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='prepuser',
            email='prep@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.dataset = Dataset.objects.create(
            dataset_name='Prep DS',
            dataset_slug='prep-ds',
            dataset_path='datasets/prep-ds/',
            total_images=4,
            total_classes=2,
            created_by=self.user,
        )
        self.media_root = Path(__file__).resolve().parents[3] / 'media' / 'datasets' / 'prep-ds'
        self.media_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        from apps.training.services.cnn.preprocessor import DatasetPreprocessorService
        import shutil
        if self.media_root.exists():
            shutil.rmtree(self.media_root.parent / 'prep-ds', ignore_errors=True)

    def test_skips_empty_image_files(self):
        from io import BytesIO
        from PIL import Image
        from apps.training.services.cnn.preprocessor import DatasetPreprocessorService

        cat_dir = self.media_root / 'cat'
        dog_dir = self.media_root / 'dog'
        cat_dir.mkdir(parents=True, exist_ok=True)
        dog_dir.mkdir(parents=True, exist_ok=True)

        def save_png(folder, name):
            path = folder / name
            Image.new('RGB', (8, 8), color='red').save(path, format='PNG')
            return path

        save_png(cat_dir, 'ok1.png')
        save_png(cat_dir, 'ok2.png')
        save_png(dog_dir, 'ok3.png')
        save_png(dog_dir, 'ok4.png')
        (cat_dir / 'bad.png').write_bytes(b'')

        cat = DatasetClass.objects.create(dataset=self.dataset, class_name='cat', class_slug='cat', total_images=3)
        dog = DatasetClass.objects.create(dataset=self.dataset, class_name='dog', class_slug='dog', total_images=2)
        for name, cls, is_train in [
            ('ok1.png', cat, True), ('ok2.png', cat, True), ('bad.png', cat, False),
            ('ok3.png', dog, True), ('ok4.png', dog, False),
        ]:
            DatasetImage.objects.create(
                dataset=self.dataset,
                dataset_class=cls,
                image_name=name,
                image_url=f'/media/datasets/prep-ds/{cls.class_slug}/{name}',
                is_train=is_train,
            )

        result = DatasetPreprocessorService.build_training_dirs(self.dataset, 99)
        try:
            self.assertEqual(result.copied, 4)
            self.assertEqual(result.skipped, ['bad.png'])
        finally:
            DatasetPreprocessorService.cleanup(result.root)


class TrainingViewTest(TestCase):
    """Test views huấn luyện."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='trainview',
            email='trainview@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.dataset = Dataset.objects.create(
            dataset_name='View DS',
            dataset_slug='view-ds',
            dataset_path='datasets/view-ds/',
            total_images=6,
            total_classes=2,
            created_by=self.user,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'trainview',
            'password': 'pass123',
        })

    def test_training_list_page(self):
        response = self.client.get(reverse('training:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cấu hình huấn luyện')
        self.assertContains(response, 'Gợi ý cấu hình huấn luyện đúng')

    @override_settings(TRAINING_SIMULATION_MODE=True)
    @patch('apps.training.services.training_service.TrainingService.launch_background')
    def test_start_training_redirect(self, mock_launch):
        response = self.client.post(reverse('training:list'), {
            'model_name': 'View CNN',
            'dataset_id': str(self.dataset.id),
            'description': '',
            'input_width': 128,
            'input_height': 128,
            'epochs': 5,
            'batch_size': 8,
            'learning_rate': 0.001,
            'optimizer': 'adam',
            'loss_function': 'categorical_crossentropy',
        })
        job = TrainingJob.objects.get(model__model_name='View CNN')
        self.assertRedirects(response, reverse('training:detail', args=[job.id]))
