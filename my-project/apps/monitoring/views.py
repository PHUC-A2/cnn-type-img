"""Views admin panel — Phase 8, chỉ role admin."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.authentication.repositories.user_repository import UserRepository
from apps.monitoring.forms import (
    AdminDatasetForm,
    AdminModelForm,
    AdminPredictionFilterForm,
    AdminSearchForm,
    AdminTrainingFilterForm,
    AdminUserCreateForm,
    AdminUserEditForm,
)
from apps.monitoring.services.admin_dashboard_service import AdminDashboardService
from apps.monitoring.services.admin_resource_service import AdminResourceService
from apps.monitoring.services.admin_user_service import AdminUserService
from core.permissions.decorators import admin_required


def _parse_page(request: HttpRequest) -> int:
    try:
        return max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        return 1


def _build_page_query(request: HttpRequest, page: int | None = None) -> str:
    params = request.GET.copy()
    if page is not None:
        params['page'] = str(page)
    elif 'page' in params:
        del params['page']
    return params.urlencode()


def _admin_context(request, section: str, **extra) -> dict:
    return {
        'page_title': 'Bảng quản trị',
        'active_nav': 'admin_panel',
        'admin_section': section,
        **extra,
    }


@admin_required
def admin_dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard tổng quan admin."""
    stats = AdminDashboardService.build_stats()
    context = _admin_context(request, 'dashboard', stats=stats)
    return render(request, 'monitoring/dashboard.html', context)


@admin_required
def admin_users_list_view(request: HttpRequest) -> HttpResponse:
    """Danh sách người dùng."""
    form = AdminSearchForm(request.GET or None)
    q = form.cleaned_data['q'] if form.is_valid() else ''
    include_inactive = form.cleaned_data.get('include_inactive', True) if form.is_valid() else True
    page = _parse_page(request)
    result = AdminUserService.list_users(q=q, include_inactive=include_inactive, page=page)

    context = _admin_context(
        request, 'users',
        form=form,
        page_result=result,
        query_string=_build_page_query(request),
        next_page_qs=_build_page_query(request, result.page + 1) if result.has_next else '',
        prev_page_qs=_build_page_query(request, result.page - 1) if result.has_prev else '',
    )
    return render(request, 'monitoring/users/list.html', context)


@admin_required
def admin_user_create_view(request: HttpRequest) -> HttpResponse:
    """Tạo người dùng mới."""
    form = AdminUserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        result = AdminUserService.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            full_name=form.cleaned_data.get('full_name', ''),
            role=form.cleaned_data['role'],
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('monitoring:users_list')
        messages.error(request, result.message)

    context = _admin_context(request, 'users', form=form, is_create=True)
    return render(request, 'monitoring/users/form.html', context)


@admin_required
def admin_user_edit_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Sửa người dùng."""
    user = UserRepository.get_by_id_any(user_id)
    if not user:
        messages.error(request, 'Không tìm thấy người dùng.')
        return redirect('monitoring:users_list')

    form = AdminUserEditForm(
        request.POST or None,
        user=user,
        initial={
            'username': user.username,
            'full_name': user.full_name or '',
            'role': user.role,
            'is_active': user.is_active,
        },
    )

    if request.method == 'POST' and form.is_valid():
        result = AdminUserService.update_user(
            user_id=user.id,
            username=form.cleaned_data['username'],
            full_name=form.cleaned_data.get('full_name', ''),
            role=form.cleaned_data['role'],
            is_active=form.cleaned_data.get('is_active', False),
            new_password=form.cleaned_data.get('new_password', ''),
            actor=request.user,
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('monitoring:users_list')
        messages.error(request, result.message)

    context = _admin_context(request, 'users', form=form, edit_user=user, is_create=False)
    return render(request, 'monitoring/users/form.html', context)


@admin_required
def admin_user_detail_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Xem chi tiết người dùng."""
    detail = AdminUserService.get_user_detail(user_id)
    if not detail:
        messages.error(request, 'Không tìm thấy người dùng.')
        return redirect('monitoring:users_list')

    context = _admin_context(request, 'users', detail=detail)
    return render(request, 'monitoring/users/detail.html', context)


@admin_required
def admin_user_delete_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Xóa user — POST."""
    if request.method != 'POST':
        return HttpResponseForbidden()
    result = AdminUserService.delete_user(user_id, request.user)
    if result.success:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect('monitoring:users_list')


@admin_required
def admin_user_deactivate_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Khóa user — POST."""
    if request.method != 'POST':
        return HttpResponseForbidden()
    result = AdminUserService.deactivate_user(user_id, request.user)
    if result.success:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect('monitoring:users_list')


@admin_required
def admin_user_activate_view(request: HttpRequest, user_id: int) -> HttpResponse:
    """Mở khóa user — POST."""
    if request.method != 'POST':
        return HttpResponseForbidden()
    result = AdminUserService.activate_user(user_id)
    if result.success:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect('monitoring:users_list')


@admin_required
def admin_datasets_list_view(request: HttpRequest) -> HttpResponse:
    form = AdminSearchForm(request.GET or None)
    q = form.cleaned_data['q'] if form.is_valid() else ''
    include_inactive = form.cleaned_data.get('include_inactive', True) if form.is_valid() else True
    page = _parse_page(request)
    result = AdminResourceService.list_datasets(q=q, include_inactive=include_inactive, page=page)
    context = _admin_context(
        request, 'datasets', form=form, page_result=result,
        query_string=_build_page_query(request),
        next_page_qs=_build_page_query(request, result.page + 1) if result.has_next else '',
        prev_page_qs=_build_page_query(request, result.page - 1) if result.has_prev else '',
    )
    return render(request, 'monitoring/datasets/list.html', context)


@admin_required
def admin_dataset_edit_view(request: HttpRequest, dataset_id: int) -> HttpResponse:
    from apps.datasets.repositories.dataset_repository import DatasetRepository

    dataset = DatasetRepository.get_by_id_any(dataset_id)
    if not dataset:
        messages.error(request, 'Không tìm thấy bộ dữ liệu.')
        return redirect('monitoring:datasets_list')

    form = AdminDatasetForm(request.POST or None, initial={
        'dataset_name': dataset.dataset_name,
        'description': dataset.description or '',
        'is_active': dataset.is_active,
    })
    if request.method == 'POST' and form.is_valid():
        result = AdminResourceService.update_dataset(
            dataset.id,
            form.cleaned_data['dataset_name'],
            form.cleaned_data.get('description', ''),
            form.cleaned_data.get('is_active', False),
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('monitoring:datasets_list')
        messages.error(request, result.message)

    context = _admin_context(request, 'datasets', form=form, dataset=dataset)
    return render(request, 'monitoring/datasets/form.html', context)


@admin_required
def admin_dataset_deactivate_view(request: HttpRequest, dataset_id: int) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseForbidden()
    result = AdminResourceService.deactivate_dataset(dataset_id)
    messages.success(request, result.message) if result.success else messages.error(request, result.message)
    return redirect('monitoring:datasets_list')


@admin_required
def admin_models_list_view(request: HttpRequest) -> HttpResponse:
    form = AdminSearchForm(request.GET or None)
    q = form.cleaned_data['q'] if form.is_valid() else ''
    include_inactive = form.cleaned_data.get('include_inactive', True) if form.is_valid() else True
    page = _parse_page(request)
    result = AdminResourceService.list_models(q=q, include_inactive=include_inactive, page=page)
    context = _admin_context(
        request, 'models', form=form, page_result=result,
        query_string=_build_page_query(request),
        next_page_qs=_build_page_query(request, result.page + 1) if result.has_next else '',
        prev_page_qs=_build_page_query(request, result.page - 1) if result.has_prev else '',
    )
    return render(request, 'monitoring/models/list.html', context)


@admin_required
def admin_model_edit_view(request: HttpRequest, model_id: int) -> HttpResponse:
    from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository

    model = CnnModelRepository.get_by_id_any(model_id)
    if not model:
        messages.error(request, 'Không tìm thấy mô hình.')
        return redirect('monitoring:models_list')

    form = AdminModelForm(request.POST or None, initial={
        'model_name': model.model_name,
        'description': model.description or '',
        'is_active': model.is_active,
    })
    if request.method == 'POST' and form.is_valid():
        result = AdminResourceService.update_model(
            model.id,
            form.cleaned_data['model_name'],
            form.cleaned_data.get('description', ''),
            form.cleaned_data.get('is_active', False),
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('monitoring:models_list')
        messages.error(request, result.message)

    context = _admin_context(request, 'models', form=form, cnn_model=model)
    return render(request, 'monitoring/models/form.html', context)


@admin_required
def admin_model_deactivate_view(request: HttpRequest, model_id: int) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseForbidden()
    result = AdminResourceService.deactivate_model(model_id)
    messages.success(request, result.message) if result.success else messages.error(request, result.message)
    return redirect('monitoring:models_list')


@admin_required
def admin_training_jobs_list_view(request: HttpRequest) -> HttpResponse:
    form = AdminTrainingFilterForm(request.GET or None)
    q = form.cleaned_data['q'] if form.is_valid() else ''
    status = form.cleaned_data.get('status', '') if form.is_valid() else ''
    page = _parse_page(request)
    result = AdminResourceService.list_training_jobs(q=q, status=status, page=page)
    context = _admin_context(
        request, 'training', form=form, page_result=result,
        query_string=_build_page_query(request),
        next_page_qs=_build_page_query(request, result.page + 1) if result.has_next else '',
        prev_page_qs=_build_page_query(request, result.page - 1) if result.has_prev else '',
    )
    return render(request, 'monitoring/training_jobs/list.html', context)


@admin_required
def admin_predictions_list_view(request: HttpRequest) -> HttpResponse:
    form = AdminPredictionFilterForm(request.GET or None)
    q = form.cleaned_data['q'] if form.is_valid() else ''
    user_id = None
    if form.is_valid() and form.cleaned_data.get('user_id'):
        try:
            user_id = int(form.cleaned_data['user_id'])
        except (TypeError, ValueError):
            user_id = None
    page = _parse_page(request)
    result = AdminResourceService.list_predictions(q=q, user_id=user_id, page=page)
    context = _admin_context(
        request, 'predictions', form=form, page_result=result,
        query_string=_build_page_query(request),
        next_page_qs=_build_page_query(request, result.page + 1) if result.has_next else '',
        prev_page_qs=_build_page_query(request, result.page - 1) if result.has_prev else '',
    )
    return render(request, 'monitoring/predictions/list.html', context)
