FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

COPY . .

ENV DJANGO_SETTINGS_MODULE=config.settings_prod
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --threads 4
