# CNN Vision Platform

Hệ thống web huấn luyện, quản lý và phân loại ảnh bằng mô hình CNN (Convolutional Neural Network) trên nền Django.

## Tính năng chính

- **Xác thực người dùng** — Đăng ký, đăng nhập, hồ sơ cá nhân
- **Quản lý dataset** — Upload ZIP (ảnh theo class), xem phân bố class
- **Huấn luyện CNN** — TensorFlow/Keras hoặc chế độ mô phỏng (không cần GPU)
- **Quản lý model** — Danh sách model, version, tải file `.h5`
- **Phân loại ảnh** — Upload ảnh, dự đoán nhãn + confidence + biểu đồ xác suất
- **Lịch sử dự đoán** — Lọc, tìm kiếm, xem chi tiết
- **Phân tích** — Dashboard biểu đồ accuracy/loss, confusion matrix
- **Admin panel** — Quản trị user, dataset, model, job, predictions, logs

## Yêu cầu hệ thống

| Thành phần | Phiên bản |
|------------|-----------|
| Python | 3.10+ |
| MySQL | 8.0+ |
| pip | Mới nhất |

## Cài đặt nhanh

### 1. Vào thư mục gốc project

Mở terminal tại thư mục chứa `manage.py` (thư mục gốc của project).

### 2. Tạo virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements\base.txt
```

### 3. Cấu hình MySQL

Tạo database trong MySQL:

```sql
CREATE DATABASE `cnn-type-img` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Sao chép và chỉnh sửa file môi trường:

```powershell
copy .env.example .env
```

Tạo `SECRET_KEY` ngẫu nhiên (chạy sau khi đã cài dependencies):

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy kết quả in ra vào `.env`.

Chỉnh các biến trong `.env`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=cnn-type-img
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_PASSWORD=admin123
```

### 4. Khởi tạo database

```powershell
.\.venv\Scripts\python.exe manage.py init_db
```

Lệnh trên chạy `migrate` và tạo tài khoản admin từ `.env`.

### 5. Chạy server

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Truy cập: **http://127.0.0.1:8000/**

| Tài khoản | Mặc định |
|-----------|----------|
| Admin | `admin` / `admin123` |
| User | Đăng ký tại `/auth/dang-ky/` |

## Cấu trúc thư mục

```
.
├── apps/
│   ├── authentication/   # Auth, dashboard, profile
│   ├── datasets/         # Upload & quản lý dataset
│   ├── training/         # Huấn luyện CNN
│   ├── models_ai/        # Quản lý model & version
│   ├── predictions/      # Phân loại ảnh & lịch sử
│   ├── analytics/        # Dashboard phân tích
│   └── monitoring/       # Admin panel & logging
├── core/                 # Middleware, permissions, enums
├── templates/            # Django templates (Aurora UI)
├── static/               # CSS, JS
├── media/                # Ảnh dataset & prediction
├── trained_models/       # File model .h5
├── tests/                # E2E tests Phase 10
├── scripts/              # Script demo bảo vệ
├── docs/                 # ERD, kiến trúc, hướng dẫn deploy
└── requirements/         # Dependencies
```

## Chạy test

```powershell
.\.venv\Scripts\python.exe manage.py test apps.authentication.tests apps.datasets.tests apps.training.tests apps.models_ai.tests apps.predictions.tests apps.analytics.tests apps.monitoring.tests tests -v 1
```

## Chế độ huấn luyện

| Chế độ | Cấu hình | Mô tả |
|--------|---------|-------|
| TensorFlow thật | `TRAINING_SIMULATION_MODE=False` | Huấn luyện CNN bằng Keras |
| Mô phỏng | `TRAINING_SIMULATION_MODE=True` | Không cần TensorFlow, phù hợp demo/máy yếu |

Nếu TensorFlow không khả dụng và `DEBUG=True`, hệ thống tự chuyển sang chế độ mô phỏng.

## Demo bảo vệ đồ án

Chạy script hướng dẫn demo:

```powershell
.\scripts\demo_defense.ps1
```

Xem thêm: [docs/architecture.md](docs/architecture.md), [docs/db.md](docs/db.md), [docs/deployment.md](docs/deployment.md)

## Luồng sử dụng (End-to-End)

```
Đăng ký / Đăng nhập
    ↓
Upload Dataset (ZIP: class1/, class2/, ...)
    ↓
Huấn luyện CNN → Lưu model .h5
    ↓
Phân loại ảnh → Nhãn + Confidence
    ↓
Xem lịch sử / Phân tích / Admin panel
```

## License

Dự án đồ án tốt nghiệp — sử dụng cho mục đích học tập.
