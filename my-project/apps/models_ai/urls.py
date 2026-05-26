"""URL routing app models_ai — Phase 4."""

from django.urls import path

from apps.models_ai import views

app_name = 'models_ai'

urlpatterns = [
    path('models/', views.model_list_view, name='list'),
    path('models/<int:model_id>/', views.model_detail_view, name='detail'),
    path('models/<int:model_id>/download/', views.model_download_view, name='download'),
    path(
        'models/<int:model_id>/versions/<int:version_id>/production/',
        views.model_set_production_view,
        name='set_production',
    ),
]
