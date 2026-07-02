from django.urls import path
from . import views

urlpatterns = [
    path('', views.hackathon_list, name='hackathon_list'),
]
