"""Views huấn luyện CNN Phase 3."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.training.forms import TrainingConfigForm
from apps.training.repositories.training_job_repository import (
    TrainingHistoryRepository,
    TrainingJobRepository,
)
from apps.training.services.training_service import TrainingService
from core.enums.training_status import TrainingStatus
from core.ml.dependencies import check_tensorflow
from core.permissions.decorators import login_required


@login_required
def training_list_view(request: HttpRequest) -> HttpResponse:
    """Danh sách job + form bắt đầu huấn luyện."""
    form = TrainingConfigForm(request.POST or None, user=request.user)
    jobs = TrainingJobRepository.list_for_user(request.user)[:20]

    if request.method == 'POST' and form.is_valid():
        result = TrainingService.start_training(
            user=request.user,
            dataset_id=form.cleaned_data['dataset_id'],
            model_name=form.cleaned_data['model_name'],
            description=form.cleaned_data.get('description', ''),
            input_width=form.cleaned_data['input_width'],
            input_height=form.cleaned_data['input_height'],
            epochs=form.cleaned_data['epochs'],
            batch_size=form.cleaned_data['batch_size'],
            learning_rate=form.cleaned_data['learning_rate'],
            optimizer=form.cleaned_data['optimizer'],
            loss_function=form.cleaned_data['loss_function'],
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('training:detail', job_id=result.job.id)
        messages.error(request, result.message)

    context = {
        'page_title': 'Huấn luyện mô hình',
        'active_nav': 'training',
        'form': form,
        'jobs': jobs,
        'training_simulation_mode': settings.TRAINING_SIMULATION_MODE,
        'tensorflow_available': check_tensorflow()[0],
    }
    return render(request, 'training/list.html', context)


@login_required
def training_detail_view(request: HttpRequest, job_id: int) -> HttpResponse:
    """Theo dõi tiến trình huấn luyện."""
    job = TrainingJobRepository.get_by_id(job_id)
    if not job:
        messages.error(request, 'Không tìm thấy job huấn luyện.')
        return redirect('training:list')
    if not TrainingJobRepository.user_can_access(request.user, job):
        return HttpResponseForbidden('Bạn không có quyền xem job này.')

    history = list(TrainingHistoryRepository.list_by_job(job.id))
    metrics = job.metrics.first()
    progress = TrainingService.get_progress_percent(job)
    is_running = job.training_status in {
        TrainingStatus.PENDING.value,
        TrainingStatus.PREPARING.value,
        TrainingStatus.TRAINING.value,
        TrainingStatus.VALIDATING.value,
    }

    context = {
        'page_title': f'Huấn luyện — {job.model.model_name}',
        'active_nav': 'training',
        'job': job,
        'history': history,
        'metrics': metrics,
        'progress': progress,
        'is_running': is_running,
        'chart_labels': [h.epoch_number for h in history],
        'chart_train_acc': [h.train_accuracy for h in history],
        'chart_val_acc': [h.validation_accuracy for h in history],
        'chart_train_loss': [h.train_loss for h in history],
        'chart_val_loss': [h.validation_loss for h in history],
    }
    return render(request, 'training/detail.html', context)


@login_required
def training_status_partial(request: HttpRequest, job_id: int) -> HttpResponse:
    """Partial HTMX — cập nhật realtime progress + logs."""
    job = TrainingJobRepository.get_by_id(job_id)
    if not job or not TrainingJobRepository.user_can_access(request.user, job):
        return HttpResponseForbidden()

    history = list(TrainingHistoryRepository.list_by_job(job.id))
    metrics = job.metrics.first()
    progress = TrainingService.get_progress_percent(job)
    is_running = job.training_status in {
        TrainingStatus.PENDING.value,
        TrainingStatus.PREPARING.value,
        TrainingStatus.TRAINING.value,
        TrainingStatus.VALIDATING.value,
    }

    context = {
        'job': job,
        'history': history,
        'metrics': metrics,
        'progress': progress,
        'is_running': is_running,
        'chart_labels': [h.epoch_number for h in history],
        'chart_train_acc': [h.train_accuracy for h in history],
        'chart_val_acc': [h.validation_accuracy for h in history],
        'chart_train_loss': [h.train_loss for h in history],
        'chart_val_loss': [h.validation_loss for h in history],
    }
    return render(request, 'training/partials/status_panel.html', context)
