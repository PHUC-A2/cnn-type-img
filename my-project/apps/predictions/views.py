"""Views phân loại ảnh — Phase 5."""

import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.predictions.forms import HistoryFilterForm, PredictForm
from apps.predictions.repositories.prediction_repository import PredictionRepository
from apps.predictions.services.prediction_history_service import PredictionHistoryService
from apps.predictions.services.prediction_display_service import PredictionDisplayService
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

    result_display = PredictionDisplayService.build_from_prediction(prediction, probabilities)

    context = {
        'page_title': 'Kết quả phân loại',
        'active_nav': 'predict',
        'prediction': prediction,
        'probabilities': probability_rows,
        'preprocess': preprocess,
        'result_display': result_display,
        'chart_labels_json': json.dumps([row.class_name for row in probabilities]),
        'chart_values_json': json.dumps([float(row.probability) for row in probabilities]),
    }
    return render(request, 'predictions/result.html', context)


def _build_page_query(request: HttpRequest, page: int | None = None) -> str:
    """Giữ nguyên bộ lọc khi chuyển trang."""
    params = request.GET.copy()
    if page is not None:
        params['page'] = str(page)
    elif 'page' in params:
        del params['page']
    return params.urlencode()


@login_required
def history_view(request: HttpRequest) -> HttpResponse:
    """Danh sách lịch sử phân loại — filter + pagination."""
    filter_form = HistoryFilterForm(request.GET or None, user=request.user)
    filters = PredictionHistoryService.parse_filters(request.GET, request.user)

    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    history = PredictionHistoryService.list_history(request.user, filters, page=page)

    context = {
        'page_title': 'Lịch sử phân loại',
        'active_nav': 'history',
        'filter_form': filter_form,
        'history': history,
        'query_string': _build_page_query(request),
        'next_page_qs': _build_page_query(request, history.page + 1) if history.has_next else '',
        'prev_page_qs': _build_page_query(request, history.page - 1) if history.has_prev else '',
    }
    return render(request, 'predictions/history.html', context)


@login_required
def history_detail_partial(request: HttpRequest, prediction_id: int) -> HttpResponse:
    """Partial HTMX — chi tiết prediction trong modal."""
    prediction = PredictionRepository.get_by_id(prediction_id)
    if not prediction or not PredictionRepository.user_can_access(request.user, prediction):
        return HttpResponseForbidden('Không có quyền xem bản ghi này.')

    probabilities = list(PredictionRepository.get_probabilities(prediction_id))
    probability_rows = [
        {'obj': row, 'percent': round(float(row.probability) * 100, 1)}
        for row in probabilities
    ]
    preprocess = getattr(prediction, 'preprocess_log', None)

    result_display = PredictionDisplayService.build_from_prediction(prediction, probabilities)

    context = {
        'prediction': prediction,
        'probabilities': probability_rows,
        'preprocess': preprocess,
        'result_display': result_display,
    }
    return render(request, 'predictions/partials/history_detail_modal.html', context)
