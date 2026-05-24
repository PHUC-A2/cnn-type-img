"""Khởi tạo database: migrate + tạo admin từ .env."""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.authentication.services.admin_init_service import AdminInitService


class Command(BaseCommand):
    help = 'Khởi tạo DB: chạy migrate và tạo tài khoản admin từ file .env'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-migrate',
            action='store_true',
            help='Bỏ qua bước migrate (chỉ tạo/kiểm tra admin)',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Đồng bộ lại admin hiện có theo .env (email, mật khẩu, role)',
        )

    def handle(self, *args, **options):
        if not options['no_migrate']:
            self.stdout.write('Running migrate...')
            call_command('migrate', interactive=False, verbosity=options['verbosity'])
            self.stdout.write(self.style.SUCCESS('Migrate done.'))

        result = AdminInitService.ensure_admin(sync=options['sync'])
        if not result.success:
            raise CommandError(f'Admin init failed: {result.message}')

        if result.created and result.user:
            self.stdout.write(self.style.SUCCESS(
                f'Admin created: {result.user.username} ({result.user.email})'
            ))
        elif result.user:
            action = 'synced' if options['sync'] else 'exists'
            self.stdout.write(self.style.WARNING(
                f'Admin {action}: {result.user.username} ({result.user.email})'
            ))
        else:
            self.stdout.write(self.style.WARNING('Admin init skipped (INIT_ADMIN_ENABLED=False).'))

        if result.user:
            self.stdout.write(
                f'  Username: {result.user.username}\n'
                f'  Email: {result.user.email}\n'
                f'  Role: {result.user.role}'
            )
