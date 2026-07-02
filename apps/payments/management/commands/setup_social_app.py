from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from apps.payments.models import SubscriptionPlan
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Sets up Site, SocialApp, and SubscriptionPlans from env vars'

    def handle(self, *args, **options):
        domain = os.environ.get('SITE_DOMAIN', 'jobs24x7.onrender.com')
        name = os.environ.get('SITE_NAME', 'Jobs24X7')

        Site.objects.exclude(pk=settings.SITE_ID).filter(domain=domain).delete()

        site = Site.objects.get(pk=settings.SITE_ID)
        old_domain = site.domain
        site.domain = domain
        site.name = name
        site.save()
        self.stdout.write(f'Updated site {settings.SITE_ID}: {old_domain} → {domain}')

        client_id = os.environ.get('GOOGLE_CLIENT_ID') or os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        if client_id and client_secret:
            app, created = SocialApp.objects.get_or_create(
                provider='google',
                client_id=client_id,
                defaults={
                    'name': 'Google',
                    'secret': client_secret,
                },
            )
            if not created:
                app.secret = client_secret
                app.save()
            if site not in app.sites.all():
                app.sites.add(site)
            self.stdout.write(f'Google SocialApp {"created" if created else "updated"}')
        else:
            self.stdout.write('GOOGLE_CLIENT_ID/SECRET not set, skipping SocialApp')

        plans_data = [
            ('weekly', 'Weekly', 99, 7, 0),
            ('monthly', 'Monthly', 299, 30, 1),
            ('six_month', '6 Months', 249, 180, 2),
            ('yearly', 'Yearly', 199, 365, 3),
        ]
        for name_slug, display, price, days, order in plans_data:
            _, created = SubscriptionPlan.objects.get_or_create(
                name=name_slug,
                defaults={
                    'display_name': display,
                    'price': price,
                    'duration_days': days,
                    'sort_order': order,
                    'features': [],
                },
            )
            if created:
                self.stdout.write(f'Plan created: {display} ₹{price}')
