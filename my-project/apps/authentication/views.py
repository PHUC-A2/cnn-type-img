"""Views xác thực và dashboard Phase 1."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.authentication.forms import LoginForm, ProfileForm, RegisterForm
from apps.authentication.services.auth_service import AuthService
from apps.authentication.services.avatar_storage_service import AvatarStorageService
from apps.authentication.services.session_service import SessionService
from apps.datasets.repositories.dataset_repository import DatasetRepository
from apps.models_ai.repositories.cnn_model_repository import CnnModelRepository
from apps.predictions.repositories.prediction_repository import PredictionRepository
from core.permissions.decorators import login_required


def home_redirect(request: HttpRequest) -> HttpResponse:
    """Trang gốc — redirect dashboard hoặc login."""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')
    return redirect('authentication:login')


def register_view(request: HttpRequest) -> HttpResponse:
    """Đăng ký tài khoản mới."""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        result = AuthService.register(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            full_name=form.cleaned_data.get('full_name', ''),
        )
        if result.success:
            messages.success(request, result.message)
            return redirect('authentication:login')
        messages.error(request, result.message)

    return render(request, 'authentication/register.html', {'form': form})


def login_view(request: HttpRequest) -> HttpResponse:
    """Đăng nhập hệ thống."""
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        result = AuthService.login(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if result.success:
            messages.success(request, result.message)
            response = redirect('authentication:dashboard')
            return SessionService.login(
                response,
                result.user,
                remember_me=form.cleaned_data.get('remember_me', False),
            )
        messages.error(request, result.message)

    return render(request, 'authentication/login.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Đăng xuất — xóa session cookie."""
    response = redirect('authentication:login')
    SessionService.logout(response)
    messages.success(request, 'Đã đăng xuất thành công.')
    return response


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard AI shell — sidebar + topbar."""
    context = {
        'page_title': 'Bảng điều khiển',
        'active_nav': 'dashboard',
        'dataset_count': DatasetRepository.list_for_user(request.user).count(),
        'model_count': CnnModelRepository.list_for_user(request.user).count(),
        'prediction_count': PredictionRepository.list_for_user(request.user).count(),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Quản lý hồ sơ cá nhân — chỉ sửa tên, username, avatar và mật khẩu."""
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        initial={
            'full_name': request.user.full_name or '',
            'username': request.user.username,
        },
    )

    if request.method == 'POST' and form.is_valid():
        result = AuthService.update_profile(
            user=request.user,
            full_name=form.cleaned_data.get('full_name', ''),
            username=form.cleaned_data['username'],
        )
        if not result.success:
            messages.error(request, result.message)
            return render(request, 'authentication/profile.html', {'form': form})

        success_message = result.message

        if form.wants_password_change():
            password_result = AuthService.change_password(
                user=request.user,
                new_password=form.cleaned_data['new_password'],
            )
            if not password_result.success:
                messages.error(request, password_result.message)
                return render(request, 'authentication/profile.html', {'form': form})
            success_message = 'Cập nhật hồ sơ và đổi mật khẩu thành công.'

        avatar_file = form.cleaned_data.get('avatar')
        if avatar_file:
            try:
                AvatarStorageService.delete_old_avatar(request.user.avatar_url)
                avatar_url = AvatarStorageService.save_avatar(avatar_file, request.user.id)
                AuthService.update_avatar(request.user, avatar_url)
            except ValueError as exc:
                messages.error(request, str(exc))
                return render(request, 'authentication/profile.html', {'form': form})

        messages.success(request, success_message)
        return redirect('authentication:profile')

    return render(request, 'authentication/profile.html', {'form': form})
