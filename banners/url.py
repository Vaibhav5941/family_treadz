from django.urls import path
from . import views

urlpatterns = [
    path('', views.banner_home, name='banner_home'),
]
