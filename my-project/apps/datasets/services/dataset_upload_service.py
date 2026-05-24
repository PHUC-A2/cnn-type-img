"""Service upload và import dataset từ file ZIP."""

import random
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.text import slugify

from apps.authentication.models import User
from apps.datasets.models import Dataset, DatasetClass, DatasetImage
from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.datasets.services.dataset_storage_service import DatasetStorageService
from apps.datasets.services.dataset_validation_service import DatasetValidationService
from apps.datasets.validators import is_zip_file


@dataclass
class DatasetUploadResult:
    """Kết quả upload dataset."""

    success: bool
    message: str
    dataset: Optional[Dataset] = None


class DatasetUploadService:
    """Xử lý upload ZIP → extract → validate → lưu DB + media."""

    TRAIN_RATIO = 0.8

    @classmethod
    def upload_from_zip(
        cls,
        user: User,
        dataset_name: str,
        zip_file: UploadedFile,
        description: str = '',
    ) -> DatasetUploadResult:
        """Pipeline upload dataset đầy đủ."""
        dataset_name = dataset_name.strip()
        description = (description or '').strip()

        if len(dataset_name) < 3:
            return DatasetUploadResult(False, 'Tên bộ dữ liệu phải có ít nhất 3 ký tự.')
        if not zip_file:
            return DatasetUploadResult(False, 'Vui lòng chọn file ZIP.')
        if not is_zip_file(zip_file.name):
            return DatasetUploadResult(False, 'Chỉ chấp nhận file ZIP.')

        max_bytes = settings.DATASET_MAX_ZIP_MB * 1024 * 1024
        if zip_file.size > max_bytes:
            return DatasetUploadResult(
                False,
                f'File ZIP không được vượt quá {settings.DATASET_MAX_ZIP_MB}MB.',
            )

        temp_dir = Path(tempfile.mkdtemp(prefix='dataset_upload_'))
        slug = DatasetStorageService.generate_unique_slug(dataset_name)

        try:
            cls._extract_zip(zip_file, temp_dir)
            root = DatasetValidationService.find_dataset_root(temp_dir / 'extracted')
            class_folders = DatasetValidationService.scan_class_folders(root)

            # Validate toàn bộ ảnh trước khi ghi DB
            for class_folder in class_folders:
                for image_path in class_folder.image_paths:
                    DatasetValidationService.validate_image_file(image_path)

            with transaction.atomic():
                dataset = DatasetRepository.create(
                    dataset_name=dataset_name,
                    dataset_slug=slug,
                    description=description or None,
                    dataset_path=DatasetStorageService.get_relative_path(slug),
                    total_images=0,
                    total_classes=len(class_folders),
                    created_by=user,
                    is_active=True,
                )

                total_images = cls._import_classes(dataset, slug, class_folders)
                dataset.total_images = total_images
                DatasetRepository.save(dataset)

            return DatasetUploadResult(
                success=True,
                message='Tải lên bộ dữ liệu thành công.',
                dataset=dataset,
            )
        except zipfile.BadZipFile:
            DatasetStorageService.remove_dataset_dir(slug)
            return DatasetUploadResult(False, 'File ZIP không hợp lệ hoặc bị hỏng.')
        except ValueError as exc:
            DatasetStorageService.remove_dataset_dir(slug)
            return DatasetUploadResult(False, str(exc))
        except Exception:
            DatasetStorageService.remove_dataset_dir(slug)
            return DatasetUploadResult(False, 'Không thể xử lý bộ dữ liệu. Vui lòng thử lại.')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _extract_zip(zip_file: UploadedFile, dest: Path) -> None:
        """Giải nén ZIP vào thư mục tạm."""
        zip_path = dest / 'upload.zip'
        with open(zip_path, 'wb') as out:
            for chunk in zip_file.chunks():
                out.write(chunk)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest / 'extracted')
        extracted = dest / 'extracted'
        if not any(extracted.iterdir()):
            raise ValueError('File ZIP rỗng.')

    @classmethod
    def _import_classes(cls, dataset: Dataset, slug: str, class_folders: list) -> int:
        """Copy ảnh, tạo class/image records và chia train/val."""
        DatasetStorageService.ensure_dataset_dir(slug)
        total_images = 0
        image_records = []

        for class_folder in class_folders:
            class_slug = slugify(class_folder.class_name) or f'class-{total_images}'
            dest_dir = DatasetStorageService.copy_class_images(
                slug, class_slug, class_folder.folder_path
            )

            dataset_class = DatasetClass.objects.create(
                dataset=dataset,
                class_name=class_folder.class_name,
                class_slug=class_slug,
                total_images=len(class_folder.image_paths),
            )

            files = sorted(f for f in dest_dir.iterdir() if f.is_file())
            random.shuffle(files)
            train_count = max(1, int(len(files) * cls.TRAIN_RATIO))

            for idx, image_path in enumerate(files):
                meta = DatasetValidationService.validate_image_file(image_path)
                is_train = idx < train_count

                image_records.append(DatasetImage(
                    dataset=dataset,
                    dataset_class=dataset_class,
                    image_name=image_path.name,
                    image_url=DatasetStorageService.build_image_url(
                        slug, class_slug, image_path.name
                    ),
                    image_format=meta.image_format,
                    mime_type=meta.mime_type,
                    width=meta.width,
                    height=meta.height,
                    channels=meta.channels,
                    file_size=meta.file_size,
                    is_train=is_train,
                ))
                total_images += 1

        if image_records:
            DatasetImage.objects.bulk_create(image_records)

        return total_images
