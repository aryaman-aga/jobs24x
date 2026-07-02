from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('update/', views.update_profile, name='update_profile'),
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    path('subscription/', views.subscription_status, name='subscription_status'),
]
