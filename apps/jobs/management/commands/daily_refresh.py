from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.jobs.models import Job
from apps.alerts.models import JobAlert
from apps.alerts.utils import send_alert_digest
from apps.payments.models import Subscription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Daily refresh: expire old jobs, send alerts'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"[{now}] Starting daily refresh...")

        expired = Job.objects.filter(is_active=True, expires_at__lte=now)
        expired_count = expired.count()
        expired.update(is_active=False)
        self.stdout.write(f"✓ Expired {expired_count} jobs")

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
