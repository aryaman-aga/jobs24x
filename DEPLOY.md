# Jobs24x — Deployment Guide
# ===========================

## Option A: Quick Deploy (Render — Free tier)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create jobs24x --public --push
```

### 2. Create a Web Service on Render
- Go to https://dashboard.render.com
- Click **New +** → **Web Service**
- Connect your GitHub repo
- Set:
  - **Name**: `jobs24x`
  - **Root Directory**: (leave blank)
  - **Runtime**: `Python 3`
  - **Build Command**: `pip install -r requirements.txt -r requirements-prod.txt && python manage.py collectstatic --noinput && python manage.py migrate`
  - **Start Command**: `gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 2 --threads 4`

### 3. Set Environment Variables
In Render dashboard → Environment:
```
DJANGO_SECRET_KEY = <generate one: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG = False
DJANGO_ALLOWED_HOSTS = .onrender.com
DJANGO_SETTINGS_MODULE = config.settings_prod
```

### 4. Add a PostgreSQL Database
- In Render, go to **New +** → **PostgreSQL**
- Copy the **Internal Database URL**
- Add it as env var: `DATABASE_URL = <internal-database-url>`

### 5. Set up Cron (Daily Refresh)
Create a **Cron Job** on Render:
- **Schedule**: `0 0 * * *`
- **Command**: `python manage.py daily_refresh`

---

## Option B: VPS (DigitalOcean / AWS EC2)

### 1. Provision a server
Ubuntu 22.04+, 1GB RAM minimum.

### 2. Install dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql nginx git
```

### 3. Clone & setup
```bash
git clone https://github.com/yourusername/jobs24x.git
cd jobs24x
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-prod.txt
```

### 4. Setup PostgreSQL
```bash
sudo -u postgres createuser jobs24x_user -P
sudo -u postgres createdb jobs24x -O jobs24x_user
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env with your values (secret key, DB credentials, etc.)
```

### 6. Migrate & collect static
```bash
export DJANGO_SETTINGS_MODULE=config.settings_prod
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_data
python manage.py createsuperuser
```

### 7. Gunicorn systemd service
Create `/etc/systemd/system/jobs24x.service`:
```
[Unit]
Description=Jobs24x Gunicorn service
After=network.target

[Service]
User=www-data
WorkingDirectory=/home/ubuntu/jobs24x
EnvironmentFile=/home/ubuntu/jobs24x/.env
ExecStart=/home/ubuntu/jobs24x/venv/bin/gunicorn config.wsgi --bind unix:/tmp/jobs24x.sock --workers 2 --threads 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now jobs24x
```

### 8. Nginx reverse proxy
Create `/etc/nginx/sites-available/jobs24x`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /home/ubuntu/jobs24x/staticfiles/;
    }
    location /media/ {
        alias /home/ubuntu/jobs24x/media/;
    }
    location / {
        proxy_pass http://unix:/tmp/jobs24x.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/jobs24x /etc/nginx/sites-enabled
sudo nginx -t && sudo systemctl reload nginx
```

### 9. SSL with Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### 10. Daily cron job
```bash
crontab -e
# Add: 0 0 * * * cd /home/ubuntu/jobs24x && source venv/bin/activate && DJANGO_SETTINGS_MODULE=config.settings_prod python manage.py daily_refresh
```

---

## Option C: Docker (Any cloud with Docker support)

```bash
cp .env.example .env
# Edit .env with your values

# Start web + db:
docker compose up -d

# Run daily refresh once:
docker compose run --rm web python manage.py daily_refresh

# Create admin:
docker compose run --rm web python manage.py createsuperuser
```

For cron with Docker, add to host crontab:
```bash
# Run daily at midnight
0 0 * * * cd /path/to/jobs24x && docker compose run --rm web python manage.py daily_refresh
```

---

## Keep-Alive (Prevent Render Free-Tier Sleep)

Render's free web services spin down after **15 minutes of inactivity**. The app has a built-in self-ping system:

### How it works
- Set `KEEP_ALIVE_URL` env var to your app's public URL
- A background thread auto-starts inside the Django process
- It pings `https://your-app.onrender.com/health/` every 10 minutes
- This generates incoming traffic → Render keeps the app awake

### Set up on Render
```bash
# In Render dashboard → Environment Variables, add:
KEEP_ALIVE_URL = https://your-app.onrender.com
```

### Verify it's working
```bash
curl https://your-app.onrender.com/health/
# → {"status": "ok", "app": "jobs24x"}
```

The server logs will show occasional `Keep-alive ping OK` messages.

### Alternative: External uptime monitors (no env var needed)
If you don't want the in-app thread, just set up a free cron job:
- **cron-job.org** → set to ping `https://your-app.onrender.com/health/` every 10 min
- **UptimeRobot** → same, free tier

---

## Post-Deploy Checklist

- [ ] All pages return 200: `/, /jobs/, /hackathons/, /pricing/, /blog/`
- [ ] Signup works: create account at `/signup/`
- [ ] Test account works: `test@jobs24x.com / test1234`
- [ ] Admin panel accessible: `/admin/`
- [ ] Daily refresh runs at midnight
- [ ] SSL working (https)
- [ ] Emails sending (check alert signup flow)
- [ ] Crontab is set for daily_refresh

---

## Useful Commands

```bash
# Add more scraped jobs
python manage.py run_scraper --count 50

# Manually refresh (expire old jobs, send alerts)
python manage.py daily_refresh

# Reset database and seed fresh data
python manage.py flush
python manage.py seed_data
python manage.py run_scraper --count 50
```
