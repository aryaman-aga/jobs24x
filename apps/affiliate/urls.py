from django.urls import path
from . import views

urlpatterns = [
    path('', views.affiliate_home, name='affiliate_home'),
    path('dashboard/', views.affiliate_dashboard, name='affiliate_dashboard'),
]
