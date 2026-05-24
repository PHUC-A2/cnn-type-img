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
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]

# Danh sách app — custom auth, không dùng django.contrib.auth/admin
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'apps.authentication',
    'apps.datasets',
    'apps.models_ai',
    'apps.training',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.authentication_middleware.AuthenticationMiddleware',
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
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
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

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
_media_root = os.getenv('MEDIA_ROOT', '').strip()
MEDIA_ROOT = Path(_media_root) if _media_root else BASE_DIR / 'media'

# Auth session cookie — signed cookie, không dùng bảng django_session
AUTH_COOKIE_NAME = 'cnn_auth_session'
AUTH_SESSION_MAX_AGE = 86400  # 1 ngày
AUTH_REMEMBER_MAX_AGE = 86400 * 14  # 14 ngày (remember me)

# Flash messages — lưu cookie, không cần session DB
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/auth/dang-nhap/'

# Khởi tạo admin — cấu hình trong .env, không hardcode nơi khác
INIT_ADMIN_ENABLED = os.getenv('INIT_ADMIN_ENABLED', 'True') == 'True'
INIT_ADMIN_USERNAME = os.getenv('INIT_ADMIN_USERNAME', 'admin')
INIT_ADMIN_EMAIL = os.getenv('INIT_ADMIN_EMAIL', 'admin@gmail.com')
INIT_ADMIN_PASSWORD = os.getenv('INIT_ADMIN_PASSWORD', 'admin123')
INIT_ADMIN_FULL_NAME = os.getenv('INIT_ADMIN_FULL_NAME', 'Quản trị viên')

# Dataset upload
DATASET_MAX_ZIP_MB = int(os.getenv('DATASET_MAX_ZIP_MB', '500'))

# Model storage + training
_model_root = os.getenv('MODEL_ROOT', '').strip()
MODEL_ROOT = Path(_model_root) if _model_root else BASE_DIR / 'trained_models'
MODEL_ROOT.mkdir(parents=True, exist_ok=True)
TRAINING_SIMULATION_MODE = os.getenv('TRAINING_SIMULATION_MODE', '').lower() in ('1', 'true', 'yes')

if not TRAINING_SIMULATION_MODE and DEBUG:
    from core.ml.dependencies import check_tensorflow as _check_tf
    _tf_available, _ = _check_tf()
    if not _tf_available:
        TRAINING_SIMULATION_MODE = True
