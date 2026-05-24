"""Management command tạo tài khoản admin mặc định."""

from django.core.management.base import BaseCommand

from apps.authentication.repositories.user_repository import UserRepository
from apps.authentication.services.password_service import PasswordService
from core.enums.user_role import UserRole


class Command(BaseCommand):
    help = 'Tạo tài khoản admin nếu chưa tồn tại'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', type=str)
        parser.add_argument('--email', default='admin@cnn.local', type=str)
        parser.add_argument('--password', default='admin123', type=str)

    def handle(self, *args, **options):
        username = options['username']
        if UserRepository.username_exists(username):
            self.stdout.write(self.style.WARNING(f'User "{username}" đã tồn tại.'))
            return

        user = UserRepository.create_user(
            username=username,
            email=options['email'],
            password=PasswordService.hash_password(options['password']),
            full_name='Quản trị viên',
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'Created admin: {user.username} / password: {options["password"]}'
        ))
