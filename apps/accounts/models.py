from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField(blank=True, default='')
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    affiliate_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_subscribed = models.BooleanField(default=False)
    subscription_end = models.DateTimeField(null=True, blank=True)
    razorpay_customer_id = models.CharField(max_length=100, blank=True, default='')
    preferred_categories = models.JSONField(default=list, blank=True)
    preferred_experience = models.CharField(max_length=20, blank=True, default='')
    preferred_location = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            referral_code=uuid.uuid4().hex[:12].upper()
        )
