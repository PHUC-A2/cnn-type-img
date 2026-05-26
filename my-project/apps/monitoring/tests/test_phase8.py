"""Test Phase 8 — Admin Panel."""

from django.test import Client, TestCase
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from core.enums.user_role import UserRole


class AdminPanelAccessTest(TestCase):
    """Kiểm tra phân quyền admin panel."""

    def setUp(self):
        self.client = Client()
        self.admin = UserRepository.create_user(
            username='paneladmin',
            email='paneladmin@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )
        self.user = UserRepository.create_user(
            username='paneluser',
            email='paneluser@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )

    def test_admin_panel_requires_login(self):
        response = self.client.get(reverse('monitoring:dashboard'))
        self.assertRedirects(response, reverse('authentication:login'))

    def test_non_admin_redirected(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneluser',
            'password': 'pass123',
        })
        response = self.client.get(reverse('monitoring:dashboard'))
        self.assertRedirects(response, reverse('authentication:dashboard'))

    def test_admin_can_access_dashboard(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bảng quản trị')

    def test_admin_users_list(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:users_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'paneladmin')
        self.assertContains(response, 'paneluser')

    def test_admin_create_user(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.post(reverse('monitoring:users_create'), {
            'username': 'newadminuser',
            'email': 'newadminuser@test.com',
            'full_name': 'New User',
            'password': 'secret12',
            'password_confirm': 'secret12',
            'role': UserRole.USER.value,
        })
        self.assertRedirects(response, reverse('monitoring:users_list'))
        created = UserRepository.get_by_username('newadminuser')
        self.assertIsNotNone(created)

    def test_admin_cannot_deactivate_self(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.post(reverse('monitoring:users_deactivate', args=[self.admin.id]))
        self.assertRedirects(response, reverse('monitoring:users_list'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_can_activate_locked_user(self):
        self.user.is_active = False
        UserRepository.save(self.user)
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.post(reverse('monitoring:users_activate', args=[self.user.id]))
        self.assertRedirects(response, reverse('monitoring:users_list'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_admin_edit_user_email_readonly(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:users_edit', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'paneluser@test.com')
        self.assertContains(response, 'Email không thể thay đổi')

        response = self.client.post(reverse('monitoring:users_edit', args=[self.user.id]), {
            'username': 'paneluser',
            'full_name': 'Updated Name',
            'role': UserRole.USER.value,
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('monitoring:users_list'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'paneluser@test.com')
        self.assertEqual(self.user.full_name, 'Updated Name')

    def test_admin_user_detail_page(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:users_detail', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'paneluser@test.com')
        self.assertContains(response, 'Thống kê hoạt động')

    def test_admin_can_delete_user(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        user_id = self.user.id
        response = self.client.post(reverse('monitoring:users_delete', args=[user_id]))
        self.assertRedirects(response, reverse('monitoring:users_list'))
        self.assertIsNone(UserRepository.get_by_id_any(user_id))

    def test_admin_cannot_delete_self(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.post(reverse('monitoring:users_delete', args=[self.admin.id]))
        self.assertRedirects(response, reverse('monitoring:users_list'))
        self.assertIsNotNone(UserRepository.get_by_id_any(self.admin.id))

    def test_admin_datasets_list(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:datasets_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_training_list(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:training_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_predictions_list(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'paneladmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:predictions_list'))
        self.assertEqual(response.status_code, 200)
