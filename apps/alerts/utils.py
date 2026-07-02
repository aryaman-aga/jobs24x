from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from apps.jobs.models import Job


def send_alert_digest(alert):
    jobs = Job.objects.filter(is_active=True)

    if alert.remote_only:
        jobs = jobs.filter(remote=True)
    if alert.role_keywords:
        from django.db.models import Q
        keywords = [k.strip() for k in alert.role_keywords.split(',')]
        q = Q()
        for kw in keywords:
            q |= Q(title__icontains=kw) | Q(description__icontains=kw) | Q(company__icontains=kw)
        jobs = jobs.filter(q)
    if alert.categories:
        jobs = jobs.filter(category__in=alert.categories)
    if alert.experience_levels:
        jobs = jobs.filter(experience_level__in=alert.experience_levels)
    if alert.min_salary:
        jobs = jobs.filter(salary_max__gte=alert.min_salary)

    jobs = jobs[:10]

    if not jobs:
        return

    unsub_url = alert.user.email
    job_lines = []
    for job in jobs:
        url = f"{'http://localhost:8000'}{reverse('job_detail', args=[job.pk])}"
        salary = f"${job.salary_min}-${job.salary_max}" if job.salary_min else "Salary not listed"
        job_lines.append(f"• {job.title} @ {job.company} ({job.location}) - {salary}\n  {url}")

    body = f"""Hi {alert.user.email},

Here are your daily job matches from Jobs24x:

{"".join(job_lines)}

Browse all jobs: http://localhost:8000/jobs/

To unsubscribe: http://localhost:8000/alerts/unsubscribe/{alert.pk}/

— Jobs24x Team
"""

    send_mail(
        subject='Your Daily Job Alert from Jobs24x',
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alert.user.email],
        fail_silently=True,
    )
