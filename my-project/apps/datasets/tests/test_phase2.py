"""Test Phase 2 — Dataset management."""

import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.datasets.models import Dataset, DatasetClass, DatasetImage
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from core.enums.user_role import UserRole


def _make_image_bytes() -> bytes:
    """Ảnh PNG 1x1 hợp lệ — tạo bằng Pillow để pass validation chặt."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', (1, 1), color='red').save(buf, format='PNG')
    return buf.getvalue()


def _make_dataset_zip(classes=None, images_per_class=2) -> bytes:
    """Tạo ZIP dataset hợp lệ: class/image.jpg."""
    classes = classes or ['cat', 'dog']
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for cls_name in classes:
            for idx in range(images_per_class):
                zf.writestr(f'{cls_name}/img_{idx}.png', _make_image_bytes())
    buf.seek(0)
    return buf.read()


class DatasetUploadServiceTest(TestCase):
    """Test service upload dataset."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='datasetuser',
            email='dataset@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )

    def test_upload_success(self):
        zip_content = _make_dataset_zip()
        uploaded = SimpleUploadedFile('animals.zip', zip_content, content_type='application/zip')
        result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Animals Test',
            zip_file=uploaded,
            description='Test dataset',
        )
        self.assertTrue(result.success, result.message)
        self.assertIsNotNone(result.dataset)
        self.assertEqual(result.dataset.total_classes, 2)
        self.assertEqual(result.dataset.total_images, 4)
        self.assertEqual(DatasetClass.objects.filter(dataset=result.dataset).count(), 2)
        self.assertEqual(DatasetImage.objects.filter(dataset=result.dataset).count(), 4)

    def test_upload_invalid_single_class(self):
        zip_content = _make_dataset_zip(classes=['only_one'])
        uploaded = SimpleUploadedFile('bad.zip', zip_content, content_type='application/zip')
        result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Bad Dataset',
            zip_file=uploaded,
        )
        self.assertFalse(result.success)
        self.assertEqual(Dataset.objects.count(), 0)

    def test_upload_not_zip(self):
        uploaded = SimpleUploadedFile('bad.txt', b'not a zip', content_type='text/plain')
        result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Bad File',
            zip_file=uploaded,
        )
        self.assertFalse(result.success)


class DatasetViewTest(TestCase):
    """Test views dataset Phase 2."""

    def setUp(self):
        self.client = Client()
        self.user = UserRepository.create_user(
            username='viewdsuser',
            email='viewds@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.client.post(reverse('authentication:login'), {
            'username': 'viewdsuser',
            'password': 'pass123',
        })

    def test_list_page(self):
        response = self.client.get(reverse('datasets:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bộ dữ liệu')

    def test_upload_page(self):
        response = self.client.get(reverse('datasets:upload'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tải lên file ZIP')

    def test_upload_flow_redirects_to_detail(self):
        zip_content = _make_dataset_zip()
        response = self.client.post(reverse('datasets:upload'), {
            'dataset_name': 'Flow Test',
            'description': 'E2E',
            'zip_file': SimpleUploadedFile('flow.zip', zip_content, content_type='application/zip'),
        })
        dataset = Dataset.objects.get(dataset_name='Flow Test')
        self.assertRedirects(response, reverse('datasets:detail', args=[dataset.id]))

    def test_detail_page(self):
        zip_content = _make_dataset_zip()
        uploaded = SimpleUploadedFile('detail.zip', zip_content, content_type='application/zip')
        result = DatasetUploadService.upload_from_zip(
            user=self.user,
            dataset_name='Detail Test',
            zip_file=uploaded,
        )
        response = self.client.get(reverse('datasets:detail', args=[result.dataset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phân bố class')
        self.assertContains(response, 'Detail Test')

    def test_list_requires_login(self):
        self.client.get(reverse('authentication:logout'))
        response = self.client.get(reverse('datasets:list'))
        self.assertRedirects(response, reverse('authentication:login'))
