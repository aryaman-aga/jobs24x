from django.contrib import admin
from .models import AffiliateReferral

@admin.register(AffiliateReferral)
class AffiliateReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_user', 'amount', 'commission_amount', 'status', 'created_at']
    list_filter = ['status']
