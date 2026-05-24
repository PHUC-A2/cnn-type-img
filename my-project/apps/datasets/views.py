"""Views quản lý bộ dữ liệu Phase 2."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.datasets.forms import DatasetUploadForm
from apps.datasets.repositories.dataset_class_repository import DatasetClassRepository
from apps.datasets.repositories.dataset_image_repository import DatasetImageRepository
from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.datasets.services.dataset_upload_service import DatasetUploadService
from core.permissions.decorators import login_required


@login_required
def dataset_list_view(request: HttpRequest) -> HttpResponse:
    """Danh sách bộ dữ liệu của user."""
    datasets = DatasetRepository.list_for_user(request.user)
    context = {
        'page_title': 'Bộ dữ liệu',
        'active_nav': 'datasets',
        'datasets': datasets,
    }
    return render(request, 'datasets/list.html', context)


@login_required
def dataset_upload_view(request: HttpRequest) -> HttpResponse:
    """Tải lên bộ dữ liệu ZIP."""
    form = DatasetUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        result = DatasetUploadService.upload_from_zip(
            user=request.user,
            dataset_name=form.cleaned_data['dataset_name'],
            zip_file=form.cleaned_data['zip_file'],
            description=form.cleaned_data.get('description', ''),
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('datasets:detail', dataset_id=result.dataset.id)
        messages.error(request, result.message)

    from django.conf import settings
    context = {
        'page_title': 'Tải lên bộ dữ liệu',
        'active_nav': 'datasets',
        'form': form,
        'max_zip_mb': settings.DATASET_MAX_ZIP_MB,
    }
    return render(request, 'datasets/upload.html', context)


@login_required
def dataset_detail_view(request: HttpRequest, dataset_id: int) -> HttpResponse:
    """Chi tiết bộ dữ liệu — class distribution + preview."""
    dataset = DatasetRepository.get_by_id(dataset_id)
    if not dataset:
        messages.error(request, 'Không tìm thấy bộ dữ liệu.')
        return redirect('datasets:list')

    if not DatasetRepository.user_can_access(request.user, dataset):
        return HttpResponseForbidden('Bạn không có quyền xem bộ dữ liệu này.')

    classes = list(DatasetClassRepository.list_by_dataset(dataset.id))
    samples = DatasetImageRepository.sample_by_dataset(dataset.id, limit=16)
    split = DatasetImageRepository.count_train_val(dataset.id)

    max_class_count = max((c.total_images for c in classes), default=1)
    class_stats = [
        {
            'obj': cls,
            'percent': round(cls.total_images / max_class_count * 100, 1),
        }
        for cls in classes
    ]

    context = {
        'page_title': dataset.dataset_name,
        'active_nav': 'datasets',
        'dataset': dataset,
        'class_stats': class_stats,
        'samples': samples,
        'split': split,
    }
    return render(request, 'datasets/detail.html', context)
