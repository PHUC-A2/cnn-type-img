"""Test Phase 9 — Logging & Monitoring."""

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from apps.monitoring.models import ApiRequestLog, SystemLog
from apps.monitoring.services.system_log_service import SystemLogService
from core.enums.log_level import LogLevel
from core.enums.user_role import UserRole


class LoggingServiceTest(TestCase):
    """Test ghi log hệ thống."""

    def test_system_log_service_creates_record(self):
        SystemLogService.info('test', 'Thông báo test', context={'key': 'value'})
        log = SystemLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.level, LogLevel.INFO.value)
        self.assertEqual(log.source, 'test')

    def test_system_log_service_error_with_trace(self):
        try:
            raise ValueError('Lỗi thử nghiệm')
        except ValueError as exc:
            SystemLogService.error('test', 'Có lỗi', exc=exc)
        log = SystemLog.objects.filter(level=LogLevel.ERROR.value).first()
        self.assertIsNotNone(log)
        self.assertIn('ValueError', log.stack_trace)


class RequestLoggingTest(TestCase):
    """Test middleware ghi api_request_logs."""

    def setUp(self):
        self.client = Client()
        self.admin = UserRepository.create_user(
            username='logadmin',
            email='logadmin@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )

    def test_request_creates_api_log(self):
        self.client.get(reverse('authentication:login'))
        self.assertTrue(ApiRequestLog.objects.exists())
        log = ApiRequestLog.objects.first()
        self.assertEqual(log.method, 'GET')
        self.assertIn('/auth/dang-nhap/', log.path)


class AdminLogsPageTest(TestCase):
    """Test trang /admin-panel/logs/."""

    def setUp(self):
        self.client = Client()
        self.admin = UserRepository.create_user(
            username='logsadmin',
            email='logsadmin@test.com',
            password=PasswordService.hash_password('admin123'),
            role=UserRole.ADMIN.value,
        )
        self.user = UserRepository.create_user(
            username='logsuser',
            email='logsuser@test.com',
            password=PasswordService.hash_password('pass123'),
            role=UserRole.USER.value,
        )
        SystemLogService.error('training', 'Job #1 thất bại')

    def test_logs_requires_admin(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'logsuser',
            'password': 'pass123',
        })
        response = self.client.get(reverse('monitoring:logs'))
        self.assertRedirects(response, reverse('authentication:dashboard'))

    def test_admin_logs_page(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'logsadmin',
            'password': 'admin123',
        })
        response = self.client.get(reverse('monitoring:logs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Job #1 thất bại')
        self.assertContains(response, 'Log hệ thống')

    @override_settings(SLOW_REQUEST_THRESHOLD_MS=0)
    def test_slow_request_tab(self):
        self.client.post(reverse('authentication:login'), {
            'username': 'logsadmin',
            'password': 'admin123',
        })
        self.client.get(reverse('authentication:login'))
        response = self.client.get(reverse('monitoring:logs'), {'tab': 'slow'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Request chậm')
