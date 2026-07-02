from django.urls import path
from . import views

urlpatterns = [
    path('', views.alert_list, name='alert_list'),
    path('create/', views.create_alert, name='create_alert'),
    path('<int:pk>/delete/', views.delete_alert, name='delete_alert'),
    path('unsubscribe/<str:token>/', views.unsubscribe_alert, name='unsubscribe_alert'),
]
