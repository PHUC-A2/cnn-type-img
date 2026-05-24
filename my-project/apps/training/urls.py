"""URL routing app training."""

from django.urls import path

from apps.training import views

app_name = 'training'

urlpatterns = [
    path('training/', views.training_list_view, name='list'),
    path('training/<int:job_id>/', views.training_detail_view, name='detail'),
    path('training/<int:job_id>/status/', views.training_status_partial, name='status'),
]
