from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import Job
from apps.hackathons.models import Hackathon
from apps.alerts.models import JobAlert
from apps.alerts.utils import send_alert_digest
from apps.payments.models import Subscription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Daily refresh: expire old jobs, expire hackathons, send alerts'

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        self.stdout.write(f"[{now}] Starting daily refresh...")

        expired = Job.objects.filter(is_active=True, expires_at__lte=now)
        expired_count = expired.count()
        expired.update(is_active=False)
        self.stdout.write(f"✓ Expired {expired_count} jobs (explicit expiry)")

        ten_days_ago = now - timedelta(days=10)
        old_no_expiry = Job.objects.filter(
            is_active=True,
            expires_at__isnull=True,
            posted_at__lte=ten_days_ago,
        )
        old_count = old_no_expiry.count()
        old_no_expiry.update(is_active=False)
        self.stdout.write(f"✓ Expired {old_count} jobs (no expiry, posted >10 days ago)")

        expired_hacks = Hackathon.objects.filter(is_active=True, end_date__lt=today)
        hacks_count = expired_hacks.count()
        expired_hacks.update(is_active=False)
        self.stdout.write(f"✓ Expired {hacks_count} hackathons (end_date passed)")

        active_alerts = JobAlert.objects.filter(is_active=True)
        sent_count = 0
        for alert in active_alerts:
            try:
                send_alert_digest(alert)
                alert.last_sent = now
                alert.save()
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send alert {alert.id}: {e}")

        self.stdout.write(f"✓ Sent {sent_count} alert digests")

        expiring_subs = Subscription.objects.filter(
            is_active=True,
            end_date__lte=now
        )
        for sub in expiring_subs:
            sub.is_active = False
            sub.save()
            profile = sub.user.profile
            profile.is_subscribed = False
            profile.save()

        self.stdout.write(f"✓ Deactivated {expiring_subs.count()} expired subscriptions")
        self.stdout.write("✓ Daily refresh complete")
