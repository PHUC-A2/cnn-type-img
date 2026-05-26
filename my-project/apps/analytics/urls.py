"""URL routing app analytics."""

from django.urls import path

from apps.analytics import views

app_name = 'analytics'

urlpatterns = [
    path('analytics/', views.analytics_view, name='index'),
]
