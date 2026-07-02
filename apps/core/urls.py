from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signed-out/', views.signed_out, name='signed_out'),
    path('signup/', views.signup, name='signup'),
    path('api/scrape/', views.scrape_now, name='scrape_now'),
]
