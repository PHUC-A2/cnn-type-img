"""URL routing chính của project."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('', include('apps.authentication.urls')),
    path('', include('apps.datasets.urls')),
    path('', include('apps.training.urls')),
    path('', include('apps.models_ai.urls')),
    path('', include('apps.predictions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
