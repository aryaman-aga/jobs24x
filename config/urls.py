from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.pages.urls')),
    path('jobs/', include('apps.jobs.urls')),
    path('hackathons/', include('apps.hackathons.urls')),
    path('pricing/', include('apps.payments.urls')),
    path('alerts/', include('apps.alerts.urls')),
    path('affiliate/', include('apps.affiliate.urls')),
    path('blog/', include('apps.blog.urls')),
    path('dashboard/', include('apps.accounts.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
