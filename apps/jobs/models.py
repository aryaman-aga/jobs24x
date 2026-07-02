from django.db import models
from django.contrib.auth.models import User


CATEGORY_CHOICES = [
    ('engineering', 'Engineering'),
    ('design', 'Design'),
    ('product', 'Product'),
    ('data_ai', 'Data & AI'),
    ('marketing', 'Marketing'),
    ('sales', 'Sales'),
    ('operations', 'Operations'),
]

EXPERIENCE_CHOICES = [
    ('fresher', 'Fresher / Intern'),
    ('junior', 'Junior'),
    ('mid', 'Mid-level'),
    ('senior', 'Senior'),
    ('lead', 'Lead / Manager+'),
]


class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    company_logo = models.URLField(blank=True, default='')
    company_url = models.URLField(blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='')
    remote = models.BooleanField(default=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, blank=True, default='')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, default='')
    description = models.TextField(blank=True, default='')
    apply_url = models.URLField()
    source_url = models.URLField(blank=True, default='')
    source_company = models.CharField(max_length=255, blank=True, default='')
    posted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-posted_at', '-created_at']
        indexes = [
            models.Index(fields=['category', 'experience_level', 'is_active']),
            models.Index(fields=['is_active', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"


class ScrapeLog(models.Model):
    run_type = models.CharField(max_length=50, default='full')
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='running')
    jobs_created = models.IntegerField(default=0)
    hackathons_created = models.IntegerField(default=0)
    jobs_expired = models.IntegerField(default=0)
    hackathons_expired = models.IntegerField(default=0)
    error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.run_type} @ {self.started_at} ({self.status})"
