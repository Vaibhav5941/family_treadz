from django.shortcuts import render
from .models import Banner

def banner_home(request):
    banners = Banner.objects.filter(is_active=True)
    return render(request, 'banners/banner_test.html', {'banners': banners})


