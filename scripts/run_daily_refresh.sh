#!/bin/bash
# Daily refresh cron job script
# Add this to crontab with: crontab -e
# Then add: 0 0 * * * /path/to/jobs24/scripts/run_daily_refresh.sh

cd /Users/aryamanagarwal/Desktop/vs_code_Aryaman/Projects/jobs24
source venv/bin/activate
python manage.py daily_refresh
