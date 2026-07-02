from django.contrib import admin
from .models import Job, SavedJob

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'category', 'experience_level', 'country', 'remote', 'is_active', 'is_featured', 'posted_at']
    list_filter = ['category', 'experience_level', 'remote', 'is_active', 'is_featured', 'country']
    search_fields = ['title', 'company', 'description']
    actions = ['mark_active', 'mark_inactive']

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = "Mark selected as active"

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = "Mark selected as inactive"

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
