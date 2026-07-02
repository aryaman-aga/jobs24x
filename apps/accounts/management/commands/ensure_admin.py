from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Creates a superuser from env vars if none exists'

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not email or not password:
            self.stdout.write('DJANGO_SUPERUSER_EMAIL/PASSWORD not set, skipping')
            return
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superuser already exists')
            return
        User.objects.create_superuser(username=email, email=email, password=password)
        self.stdout.write(f'Superuser created: {email}')
