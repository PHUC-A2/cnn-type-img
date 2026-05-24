"""Test khởi tạo admin từ .env."""

from django.test import TestCase, override_settings

from apps.authentication.models import User
from apps.authentication.services.admin_init_service import AdminInitService
from apps.authentication.services.password_service import PasswordService
from core.enums.user_role import UserRole


@override_settings(
    INIT_ADMIN_ENABLED=True,
    INIT_ADMIN_USERNAME='env_admin',
    INIT_ADMIN_EMAIL='env_admin@test.com',
    INIT_ADMIN_PASSWORD='secret123',
    INIT_ADMIN_FULL_NAME='Admin từ ENV',
)
class AdminInitServiceTest(TestCase):
    """Test AdminInitService đọc cấu hình từ settings/.env."""

    def test_create_admin_from_env(self):
        result = AdminInitService.ensure_admin()
        self.assertTrue(result.success)
        self.assertTrue(result.created)
        self.assertEqual(result.user.username, 'env_admin')
        self.assertEqual(result.user.email, 'env_admin@test.com')
        self.assertEqual(result.user.role, UserRole.ADMIN.value)
        self.assertTrue(
            PasswordService.verify_password('secret123', result.user.password)
        )

    def test_skip_when_admin_exists(self):
        AdminInitService.ensure_admin()
        result = AdminInitService.ensure_admin()
        self.assertTrue(result.success)
        self.assertFalse(result.created)
        self.assertEqual(User.objects.filter(username='env_admin').count(), 1)

    def test_sync_updates_password_from_env(self):
        AdminInitService.ensure_admin()
        with override_settings(INIT_ADMIN_PASSWORD='newpass456'):
            result = AdminInitService.ensure_admin(sync=True)
        self.assertTrue(result.success)
        user = User.objects.get(username='env_admin')
        self.assertTrue(PasswordService.verify_password('newpass456', user.password))

    def test_disabled_skips_init(self):
        with override_settings(INIT_ADMIN_ENABLED=False):
            result = AdminInitService.ensure_admin()
        self.assertTrue(result.success)
        self.assertFalse(result.created)
        self.assertIsNone(result.user)
