from django.db import models
from django.contrib.auth.models import User


MODE_CHOICES = [
    ('online', 'Online'),
    ('in_person', 'In-person'),
    ('hybrid', 'Hybrid'),
]

HACKATHON_CATEGORIES = [
    ('ai', 'AI'),
    ('web3', 'Web3'),
    ('climate', 'Climate'),
    ('health', 'Health'),
    ('fintech', 'Fintech'),
    ('gaming', 'Gaming'),
    ('student', 'Student'),
    ('beginner', 'Beginner'),
    ('iot', 'IoT'),
    ('ar_vr', 'AR/VR'),
    ('edtech', 'EdTech'),
    ('other', 'Other'),
]


class Hackathon(models.Model):
    title = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='online')
    category = models.CharField(max_length=20, choices=HACKATHON_CATEGORIES, default='other')
    prize_pool = models.CharField(max_length=100, blank=True, default='')
    start_date = models.DateField()
    end_date = models.DateField()
    apply_url = models.URLField()
    description = models.TextField(blank=True, default='')
    cover_image = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.title


class HackathonApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hackathon_apps')
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'hackathon')
        ordering = ['-applied_at']

    def __str__(self):
        return f'{self.user.email} → {self.hackathon.title}'
