"""URL routing admin panel."""

from django.urls import path

from apps.monitoring import views

app_name = 'monitoring'

urlpatterns = [
    path('admin-panel/', views.admin_dashboard_view, name='dashboard'),
    path('admin-panel/users/', views.admin_users_list_view, name='users_list'),
    path('admin-panel/users/create/', views.admin_user_create_view, name='users_create'),
    path('admin-panel/users/<int:user_id>/', views.admin_user_detail_view, name='users_detail'),
    path('admin-panel/users/<int:user_id>/edit/', views.admin_user_edit_view, name='users_edit'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_user_delete_view, name='users_delete'),
    path('admin-panel/users/<int:user_id>/deactivate/', views.admin_user_deactivate_view, name='users_deactivate'),
    path('admin-panel/users/<int:user_id>/activate/', views.admin_user_activate_view, name='users_activate'),
    path('admin-panel/datasets/', views.admin_datasets_list_view, name='datasets_list'),
    path('admin-panel/datasets/<int:dataset_id>/edit/', views.admin_dataset_edit_view, name='datasets_edit'),
    path('admin-panel/datasets/<int:dataset_id>/deactivate/', views.admin_dataset_deactivate_view, name='datasets_deactivate'),
    path('admin-panel/models/', views.admin_models_list_view, name='models_list'),
    path('admin-panel/models/<int:model_id>/edit/', views.admin_model_edit_view, name='models_edit'),
    path('admin-panel/models/<int:model_id>/deactivate/', views.admin_model_deactivate_view, name='models_deactivate'),
    path('admin-panel/training-jobs/', views.admin_training_jobs_list_view, name='training_list'),
    path('admin-panel/predictions/', views.admin_predictions_list_view, name='predictions_list'),
    path('admin-panel/logs/', views.admin_logs_view, name='logs'),
]
