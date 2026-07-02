from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('save/<int:pk>/', views.save_job, name='save_job'),
    path('unsave/<int:pk>/', views.unsave_job, name='unsave_job'),
]
