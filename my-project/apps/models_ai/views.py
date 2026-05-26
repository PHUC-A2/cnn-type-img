"""Views quản lý mô hình CNN — Phase 4."""

from django.contrib import messages
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.models_ai.repositories.model_version_repository import ModelVersionRepository
from apps.models_ai.services.model_catalog_service import ModelCatalogService
from apps.models_ai.services.model_loader_service import ModelLoaderService
from apps.models_ai.services.model_version_service import ModelVersionService
from core.permissions.decorators import login_required


@login_required
def model_list_view(request: HttpRequest) -> HttpResponse:
    """Danh sách mô hình CNN — card grid kèm accuracy và production."""
    cards = ModelCatalogService.build_list_cards(request.user)
    context = {
        'page_title': 'Mô hình CNN',
        'active_nav': 'models',
        'cards': cards,
    }
    return render(request, 'models/list.html', context)


@login_required
def model_detail_view(request: HttpRequest, model_id: int) -> HttpResponse:
    """Chi tiết mô hình — metadata, phiên bản, liên kết job huấn luyện."""
    detail = ModelCatalogService.build_detail(request.user, model_id)
    if not detail:
        messages.error(request, 'Không tìm thấy mô hình hoặc bạn không có quyền truy cập.')
        return redirect('models_ai:list')

    context = {
        'page_title': detail.model.model_name,
        'active_nav': 'models',
        'detail': detail,
    }
    return render(request, 'models/detail.html', context)


@login_required
def model_download_view(request: HttpRequest, model_id: int) -> HttpResponse:
    """Tải xuống file .h5 — mặc định lấy bản production."""
    cnn = CnnModelRepository.get_by_id(model_id)
    if not cnn or not CnnModelRepository.user_can_access(request.user, cnn):
        return HttpResponseForbidden('Bạn không có quyền tải mô hình này.')

    version_id = request.GET.get('version_id')
    version = None
    if version_id:
        try:
            version = ModelVersionRepository.get_by_id(int(version_id))
        except (TypeError, ValueError):
            version = None
        if not version or version.model_id != cnn.id:
            messages.error(request, 'Phiên bản mô hình không hợp lệ.')
            return redirect('models_ai:detail', model_id=model_id)
    else:
        version = ModelVersionRepository.get_production(cnn.id)
        if not version and cnn.model_file_path:
            ModelVersionService.sync_missing_versions()
            version = ModelVersionRepository.get_production(cnn.id)

    if not version:
        messages.error(request, 'Mô hình chưa có file để tải xuống.')
        return redirect('models_ai:detail', model_id=model_id)

    try:
        file_path = ModelLoaderService.get_download_path(cnn, version)
    except FileNotFoundError:
        messages.error(request, 'File model không tồn tại trên hệ thống.')
        return redirect('models_ai:detail', model_id=model_id)

    filename = ModelLoaderService.build_download_filename(cnn, version)
    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    response['Content-Type'] = 'application/octet-stream'
    return response


@login_required
def model_set_production_view(request: HttpRequest, model_id: int, version_id: int) -> HttpResponse:
    """Đặt phiên bản làm production — POST only."""
    if request.method != 'POST':
        return redirect('models_ai:detail', model_id=model_id)

    cnn = CnnModelRepository.get_by_id(model_id)
    if not cnn or not CnnModelRepository.user_can_access(request.user, cnn):
        return HttpResponseForbidden('Bạn không có quyền thao tác mô hình này.')

    result = ModelVersionService.set_production(model_id, version_id)
    if result.success:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)

    return redirect('models_ai:detail', model_id=model_id)
