"""URL routing app predictions."""

from django.urls import path

from apps.predictions import views

app_name = 'predictions'

urlpatterns = [
    path('predict/', views.predict_view, name='predict'),
    path('predict/result/<int:prediction_id>/', views.predict_result_view, name='result'),
]
