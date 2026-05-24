"""URL routing chính của project."""

from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
]
