from django.contrib import admin
from .models import JobAlert

@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'role_keywords', 'is_active', 'frequency', 'last_sent']
    list_filter = ['is_active', 'frequency']
