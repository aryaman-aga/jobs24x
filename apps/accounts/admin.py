from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_subscribed', 'subscription_end', 'affiliate_balance', 'referral_code']
    search_fields = ['user__email', 'referral_code']
