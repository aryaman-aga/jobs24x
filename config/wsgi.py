import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.wsgi import get_wsgi_application

from apps.core.scheduler import start_scheduler

application = get_wsgi_application()

start_scheduler()
