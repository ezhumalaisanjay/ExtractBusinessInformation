#!/bin/bash

# Navigate to app directory
cd /var/www/html/linkedin-scraper

# Activate virtual environment
source venv/bin/activate

# Start application with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --reuse-port --reload main:app > /var/log/linkedin-scraper.log 2>&1 &

# Save the process ID to stop it later
echo $! > /var/www/html/linkedin-scraper/gunicorn.pid