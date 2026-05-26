"""Test hiển thị kết quả phân loại."""

from django.test import TestCase

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.models_ai.models import CnnModel
from apps.predictions.models import Prediction, PredictionProbability
from apps.predictions.services.prediction_display_service import PredictionDisplayService
from core.enums.user_role import UserRole


class PredictionDisplayServiceTest(TestCase):
    """Test chuyển kết quả sang mô tả tiếng Việt."""

    def setUp(self):
        self.user = UserRepository.create_user(
            username='displayuser',
            email='display@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        self.model = CnnModel.objects.create(
            model_name='Display Model',
            model_slug='display-model',
            input_width=128,
            input_height=128,
            created_by=self.user,
        )
        self.prediction = Prediction.objects.create(
            model=self.model,
            predicted_by=self.user,
            image_name='dog.png',
            image_url='/media/predictions/dog.png',
            predicted_class='dog',
            confidence_score=0.87,
            top_k=2,
        )
        PredictionProbability.objects.create(
            prediction=self.prediction,
            class_name='dog',
            probability=0.87,
            rank_order=1,
        )
        PredictionProbability.objects.create(
            prediction=self.prediction,
            class_name='cat',
            probability=0.10,
            rank_order=2,
        )

    def test_build_verdict_for_dog(self):
        display = PredictionDisplayService.build_from_prediction(self.prediction)
        self.assertEqual(display.verdict_label, 'Con chó')
        self.assertEqual(display.category_label, 'Động vật')
        self.assertEqual(display.confidence_percent, 87.0)
        self.assertEqual(len(display.alternatives), 2)
        self.assertTrue(display.alternatives[0].is_winner)
        self.assertIn('Không phải', display.alternatives[1].comparison_text)

    def test_result_page_shows_verdict(self):
        from django.test import Client
        from django.urls import reverse

        client = Client()
        client.post(reverse('authentication:login'), {
            'username': 'displayuser',
            'password': 'pass123',
        })
        response = client.get(reverse('predictions:result', args=[self.prediction.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ảnh trên là:')
        self.assertContains(response, 'Con chó')
        self.assertContains(response, 'So sánh với các class khác')
