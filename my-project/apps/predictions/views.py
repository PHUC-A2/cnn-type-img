"""Views phân loại ảnh — Phase 5."""

import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.predictions.forms import PredictForm
from apps.predictions.repositories.prediction_repository import PredictionRepository
from apps.predictions.services.prediction_service import PredictionService
from apps.predictions.services.prediction_storage_service import PredictionStorageService
from core.permissions.decorators import login_required


def _predict_guide_context() -> dict:
    """Context dùng chung cho alert hướng dẫn trang phân loại."""
    ext_list = sorted(ext.lstrip('.').upper() for ext in PredictionStorageService.ALLOWED_EXTENSIONS)
    return {
        'max_image_mb': PredictionStorageService.MAX_SIZE_MB,
        'allowed_image_ext_display': ', '.join(ext_list),
        'training_simulation_mode': settings.TRAINING_SIMULATION_MODE,
    }


@login_required
def predict_view(request: HttpRequest) -> HttpResponse:
    """Upload ảnh và chọn model để phân loại."""
    form = PredictForm(request.POST or None, request.FILES or None, user=request.user)
    ready_models = PredictionService.list_ready_models(request.user)

    if request.method == 'POST' and form.is_valid():
        result = PredictionService.run_prediction(
            user=request.user,
            model_id=form.cleaned_data['model_id'],
            image_file=form.cleaned_data['image'],
            top_k=form.cleaned_data['top_k'],
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('predictions:result', prediction_id=result.prediction.id)
        messages.error(request, result.message)

    context = {
        'page_title': 'Phân loại ảnh',
        'active_nav': 'predict',
        'form': form,
        'ready_models': ready_models,
        **_predict_guide_context(),
    }
    return render(request, 'predictions/predict.html', context)


@login_required
def predict_result_view(request: HttpRequest, prediction_id: int) -> HttpResponse:
    """Hiển thị kết quả phân loại + biểu đồ xác suất."""
    prediction = PredictionRepository.get_by_id(prediction_id)
    if not prediction:
        messages.error(request, 'Không tìm thấy kết quả phân loại.')
        return redirect('predictions:predict')
    if not PredictionRepository.user_can_access(request.user, prediction):
        return HttpResponseForbidden('Bạn không có quyền xem kết quả này.')

    probabilities = list(PredictionRepository.get_probabilities(prediction_id))
    preprocess = getattr(prediction, 'preprocess_log', None)
    probability_rows = [
        {'obj': row, 'percent': round(float(row.probability) * 100, 1)}
        for row in probabilities
    ]

    context = {
        'page_title': 'Kết quả phân loại',
        'active_nav': 'predict',
        'prediction': prediction,
        'probabilities': probability_rows,
        'preprocess': preprocess,
        'chart_labels_json': json.dumps([row.class_name for row in probabilities]),
        'chart_values_json': json.dumps([float(row.probability) for row in probabilities]),
    }
    return render(request, 'predictions/result.html', context)
