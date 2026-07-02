from django.contrib import admin
from .models import Hackathon

@admin.register(Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'mode', 'category', 'start_date', 'end_date', 'is_active']
    list_filter = ['mode', 'category', 'is_active']
    search_fields = ['title', 'organizer']
