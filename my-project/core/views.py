"""View cơ bản cho trang chủ."""

from django.shortcuts import render


def hello_world(request):
    """Trang Hello World — xác nhận server hoạt động."""
    return render(request, 'core/hello.html')
