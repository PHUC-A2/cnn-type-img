"""URL routing app datasets."""

from django.urls import path

from apps.datasets import views

app_name = 'datasets'

urlpatterns = [
    path('datasets/', views.dataset_list_view, name='list'),
    path('datasets/upload/', views.dataset_upload_view, name='upload'),
    path('datasets/<int:dataset_id>/', views.dataset_detail_view, name='detail'),
]
