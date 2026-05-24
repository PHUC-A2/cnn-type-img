from django.db import models

from core.enums.user_role import UserRole


class User(models.Model):
    """Model người dùng — map bảng `users` theo db.md."""

    username = models.CharField(max_length=50, unique=True, verbose_name='Tên đăng nhập')
    email = models.EmailField(max_length=100, unique=True, verbose_name='Email')
    password = models.CharField(max_length=255, verbose_name='Mật khẩu')
    full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Họ tên')
    avatar_url = models.CharField(max_length=500, blank=True, null=True, verbose_name='Avatar URL')
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices(),
        default=UserRole.USER.value,
        verbose_name='Vai trò',
    )
    is_active = models.BooleanField(default=True, verbose_name='Kích hoạt')
    last_login = models.DateTimeField(blank=True, null=True, verbose_name='Lần đăng nhập cuối')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'users'
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.username

    @property
    def is_authenticated(self) -> bool:
        # Thuộc tính bắt buộc để middleware/decorator nhận diện user đã login
        return True

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    def get_display_name(self) -> str:
        return self.full_name or self.username
