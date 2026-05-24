"""URL routing app authentication."""

from django.urls import path

from apps.authentication import views

app_name = 'authentication'

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('auth/dang-ky/', views.register_view, name='register'),
    path('auth/dang-nhap/', views.login_view, name='login'),
    path('auth/dang-xuat/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]
