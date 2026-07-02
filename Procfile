web: gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 2 --threads 4
release: python manage.py migrate --noinput
worker: python manage.py daily_refresh
