from django.db import models
from django.contrib.auth.models import User


class JobAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    role_keywords = models.CharField(max_length=500, default='')
    experience_levels = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    locations = models.JSONField(default=list, blank=True)
    remote_only = models.BooleanField(default=True)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, default='daily')
    last_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert for {self.user.email}: {self.role_keywords[:30]}"
