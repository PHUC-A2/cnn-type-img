# Hướng dẫn triển khai (Deployment) — CNN Vision Platform

## 1. Yêu cầu server

| Thành phần | Khuyến nghị |
|------------|-------------|
| OS | Ubuntu 22.04 LTS / Windows Server |
| RAM | Tối thiểu 4 GB (8 GB+ nếu huấn luyện TensorFlow thật) |
| CPU | 2+ cores |
| Disk | 20 GB+ (ảnh dataset + model .h5) |
| Python | 3.10 hoặc 3.11 |
| MySQL | 8.0+ |
| Web server | Nginx + Gunicorn (Linux) hoặc Waitress (Windows) |

## 2. Chuẩn bị MySQL

```sql
CREATE DATABASE `cnn-type-img` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cnn_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON `cnn-type-img`.* TO 'cnn_user'@'localhost';
FLUSH PRIVILEGES;
```

## 3. Cài đặt ứng dụng

```bash
cd /opt/cnn-platform/my-project
python3 -m venv .venv
source .venv/bin/activate   # Linux
# .\.venv\Scripts\Activate.ps1   # Windows

pip install --upgrade pip
pip install -r requirements/base.txt
pip install gunicorn        # Linux
# pip install waitress      # Windows (tùy chọn)
```

## 4. Cấu hình môi trường production

Tạo file `.env`:

```env
SECRET_KEY=<random-50-chars-secret>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,127.0.0.1

DB_NAME=cnn-type-img
DB_USER=cnn_user
DB_PASSWORD=strong_password_here
DB_HOST=127.0.0.1
DB_PORT=3306

MEDIA_URL=/media/
# MEDIA_ROOT=/var/www/cnn-platform/media
# MODEL_ROOT=/var/www/cnn-platform/trained_models

INIT_ADMIN_ENABLED=True
INIT_ADMIN_USERNAME=admin
INIT_ADMIN_PASSWORD=<change-me>
INIT_ADMIN_EMAIL=admin@yourdomain.com

TRAINING_SIMULATION_MODE=False
SLOW_REQUEST_THRESHOLD_MS=1000
DATASET_MAX_ZIP_MB=500
```

**Lưu ý bảo mật:**
- Đặt `DEBUG=False`
- Đổi `SECRET_KEY` và mật khẩu admin
- Không commit file `.env` lên git

## 5. Khởi tạo database & static

```bash
python manage.py init_db
python manage.py collectstatic --noinput
```

Tạo thư mục lưu trữ (nếu dùng đường dẫn tuyệt đối):

```bash
mkdir -p /var/www/cnn-platform/media
mkdir -p /var/www/cnn-platform/trained_models
mkdir -p /var/www/cnn-platform/logs
chown -R www-data:www-data /var/www/cnn-platform
```

## 6. Chạy với Gunicorn (Linux)

```bash
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile /var/log/cnn-platform/access.log \
  --error-logfile /var/log/cnn-platform/error.log
```

> `--timeout 120` cần thiết vì upload dataset và huấn luyện có thể mất thời gian.

### Systemd service

Tạo `/etc/systemd/system/cnn-platform.service`:

```ini
[Unit]
Description=CNN Vision Platform
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/cnn-platform/my-project
EnvironmentFile=/opt/cnn-platform/my-project/.env
ExecStart=/opt/cnn-platform/my-project/.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cnn-platform
sudo systemctl start cnn-platform
```

## 7. Cấu hình Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    client_max_body_size 500M;

    location /static/ {
        alias /opt/cnn-platform/my-project/staticfiles/;
    }

    location /media/ {
        alias /var/www/cnn-platform/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Bật HTTPS với Let's Encrypt:

```bash
sudo certbot --nginx -d yourdomain.com
```

## 8. Triển khai trên Windows (IIS / Waitress)

```powershell
pip install waitress
waitress-serve --port=8000 config.wsgi:application
```

Hoặc dùng IIS với wfastcgi — cấu hình tương tự, đảm bảo quyền ghi cho `media/` và `trained_models/`.

## 9. TensorFlow trên production

| Môi trường | Khuyến nghị |
|------------|-------------|
| Demo / máy yếu | `TRAINING_SIMULATION_MODE=True` |
| Production có GPU | `TRAINING_SIMULATION_MODE=False`, cài `tensorflow` phù hợp CUDA |
| Production không GPU | Simulation mode hoặc huấn luyện offline rồi upload model |

Kiểm tra TensorFlow:

```bash
python -c "import tensorflow as tf; print(tf.__version__)"
```

## 10. Backup

| Dữ liệu | Cách backup |
|---------|-------------|
| Database | `mysqldump cnn-type-img > backup.sql` |
| Ảnh | Copy thư mục `media/` |
| Model | Copy thư mục `trained_models/` |
| Logs | Copy thư mục `logs/` |

Lịch backup khuyến nghị: hàng ngày (DB), hàng tuần (media + models).

## 11. Monitoring

- **Admin panel logs:** `/admin-panel/logs/` — system logs + slow requests + CPU/RAM
- **Loguru files:** `logs/app/`, `logs/training/`, `logs/prediction/`
- **Health check:** GET `/auth/dang-nhap/` → status 200

## 12. Checklist trước go-live

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` đã đổi
- [ ] Mật khẩu admin đã đổi
- [ ] MySQL user riêng (không dùng root)
- [ ] HTTPS đã bật
- [ ] `client_max_body_size` đủ lớn cho upload ZIP
- [ ] Quyền ghi `media/`, `trained_models/`, `logs/`
- [ ] Chạy full test suite thành công
- [ ] Backup strategy đã thiết lập

## 13. Chạy test trước deploy

```powershell
.\.venv\Scripts\python.exe manage.py test apps.authentication.tests apps.datasets.tests apps.training.tests apps.models_ai.tests apps.predictions.tests apps.analytics.tests apps.monitoring.tests tests -v 1
```
