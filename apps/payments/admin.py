from django.contrib import admin
from .models import SubscriptionPlan, Subscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'price', 'duration_days', 'is_active', 'sort_order']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount_paid', 'is_active', 'is_cancelled', 'start_date', 'end_date']
    list_filter = ['is_active', 'is_cancelled', 'plan']
    search_fields = ['user__email']
