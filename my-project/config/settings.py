"""
Cấu hình Django cho hệ thống CNN Image Classification.
Đọc biến môi trường từ .env, kết nối MySQL.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Thư mục gốc project (my-project/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp biến môi trường từ file .env
load_dotenv(BASE_DIR / '.env')


def env_required(name: str) -> str:
    """Lấy biến môi trường bắt buộc — thiếu trong .env thì dừng khởi động."""
    if name not in os.environ:
        raise ImproperlyConfigured(f'Biến môi trường {name} chưa được cấu hình trong .env')
    return os.environ[name]

# Khóa bảo mật — bắt buộc đổi khi deploy production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# Chế độ debug — tắt khi lên production
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Danh sách app — không dùng DB mặc định của Django (auth/admin/sessions)
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — MySQL, toàn bộ cấu hình lấy từ .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env_required('DB_NAME'),
        'USER': env_required('DB_USER'),
        'PASSWORD': env_required('DB_PASSWORD'),
        'HOST': env_required('DB_HOST'),
        'PORT': env_required('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files — cấu trúc sẵn sàng cho Tailwind CSS
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
