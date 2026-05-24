"""Test cases Phase 1 — Auth + Dashboard."""

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.authentication.models import User
from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.auth_service import AuthService
from apps.authentication.services.password_service import PasswordService
from apps.authentication.services.session_service import SessionService
from core.enums.user_role import UserRole


class UserModelTest(TestCase):
    """Test model User — bảng users."""

    def test_create_user_in_db(self):
        user = UserRepository.create_user(
            username='testuser',
            email='test@example.com',
            password=PasswordService.hash_password('secret123'),
            role=UserRole.USER.value,
        )
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)
        self.assertEqual(user.role, 'user')
        self.assertTrue(user.is_active)

    def test_db_table_name_is_users(self):
        self.assertEqual(User._meta.db_table, 'users')


class AuthServiceTest(TestCase):
    """Test service đăng ký / đăng nhập."""

    def test_register_success(self):
        result = AuthService.register(
            username='newuser',
            email='new@example.com',
            password='password123',
            full_name='Nguyen Van A',
        )
        self.assertTrue(result.success)
        self.assertEqual(result.user.username, 'newuser')

    def test_register_duplicate_username(self):
        AuthService.register('dupuser', 'a@test.com', 'password123')
        result = AuthService.register('dupuser', 'b@test.com', 'password123')
        self.assertFalse(result.success)

    def test_login_success(self):
        AuthService.register('loginuser', 'login@test.com', 'password123')
        result = AuthService.login('loginuser', 'password123')
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user.last_login)

    def test_login_wrong_password(self):
        AuthService.register('wrongpass', 'wp@test.com', 'password123')
        result = AuthService.login('wrongpass', 'wrong')
        self.assertFalse(result.success)


class AuthViewTest(TestCase):
    """Test views Phase 1 — HTTP flow."""

    def setUp(self):
        self.client = Client()
        AuthService.register('viewuser', 'view@test.com', 'password123', 'View User')

    def test_home_redirects_to_login_when_anonymous(self):
        response = self.client.get(reverse('authentication:home'))
        self.assertRedirects(response, reverse('authentication:login'))

    def test_register_page_get(self):
        response = self.client.get(reverse('authentication:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Đăng ký')

    def test_login_and_dashboard_flow(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'viewuser',
            'password': 'password123',
        })
        self.assertRedirects(response, reverse('authentication:dashboard'))
        response = self.client.get(reverse('authentication:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bảng điều khiển')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('authentication:dashboard'))
        self.assertRedirects(response, reverse('authentication:login'))

    def test_logout_clears_session(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'viewuser',
            'password': 'password123',
        })
        response = self.client.get(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('authentication:login'))
        response = self.client.get(reverse('authentication:dashboard'))
        self.assertRedirects(response, reverse('authentication:login'))

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse('authentication:profile'))
        self.assertRedirects(response, reverse('authentication:login'))

    def test_profile_update(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'viewuser',
            'password': 'password123',
        })
        response = self.client.post(reverse('authentication:profile'), {
            'full_name': 'Updated Name',
            'email': 'updated@test.com',
        })
        self.assertRedirects(response, reverse('authentication:profile'))
        user = UserRepository.get_by_username('viewuser')
        self.assertEqual(user.full_name, 'Updated Name')
        self.assertEqual(user.email, 'updated@test.com')


class AdminRoleTest(TestCase):
    """Test phân quyền admin/user."""

    def setUp(self):
        self.client = Client()
        UserRepository.create_user(
            username='adminuser',
            email='admin@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )

    def test_admin_sees_admin_menu_on_dashboard(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'adminuser',
            'password': 'admin123',
        })
        response = self.client.get(reverse('authentication:dashboard'))
        self.assertContains(response, 'Bảng quản trị')
        self.assertContains(response, 'Quản trị viên')


class SessionServiceTest(TestCase):
    """Test signed cookie session."""

    @override_settings(
        AUTH_COOKIE_NAME='test_auth_cookie',
        AUTH_SESSION_MAX_AGE=3600,
        AUTH_REMEMBER_MAX_AGE=86400,
    )
    def test_session_cookie_login_logout(self):
        user = UserRepository.create_user(
            username='sessionuser',
            email='session@test.com',
            password=PasswordService.hash_password('pass'),
            role=UserRole.USER.value,
        )
        client = Client()
        response = client.post(reverse('authentication:login'), {
            'username': 'sessionuser',
            'password': 'pass',
            'remember_me': True,
        })
        self.assertIn('test_auth_cookie', response.cookies)

        response = client.get(reverse('authentication:dashboard'))
        self.assertEqual(response.status_code, 200)

        response = client.get(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('authentication:login'))


class NoDjangoDefaultTablesTest(TestCase):
    """Đảm bảo không tạo bảng Django mặc định."""

    def test_only_users_table_exists(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SHOW TABLES')
            tables = {row[0] for row in cursor.fetchall()}
        self.assertIn('users', tables)
        self.assertNotIn('auth_user', tables)
        self.assertNotIn('django_session', tables)
        self.assertNotIn('django_admin_log', tables)
