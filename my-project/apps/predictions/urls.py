"""URL routing app predictions."""

from django.urls import path

from apps.predictions import views

app_name = 'predictions'

urlpatterns = [
    path('predict/', views.predict_view, name='predict'),
    path('predict/result/<int:prediction_id>/', views.predict_result_view, name='result'),
    path('history/', views.history_view, name='history'),
    path('history/<int:prediction_id>/detail/', views.history_detail_partial, name='history_detail'),
]
