#!/bin/bash

# Navigate to app directory
cd /var/www/html/linkedin-scraper

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    virtualenv -p python3 venv
fi

# Activate virtual environment
source venv/bin/activate

# Install app dependencies
pip install -e .

# Set environment variables
if [ ! -f ".env" ]; then
    echo "Creating environment file..."
    echo "FLASK_APP=main.py" > .env
    echo "FLASK_ENV=production" >> .env
    
    # Add LinkedIn credentials if provided as environment variables
    if [ ! -z "$LINKEDIN_EMAIL" ] && [ ! -z "$LINKEDIN_PASSWORD" ]; then
        echo "LINKEDIN_EMAIL=$LINKEDIN_EMAIL" >> .env
        echo "LINKEDIN_PASSWORD=$LINKEDIN_PASSWORD" >> .env
    fi
fi

# Ensure proper permissions
chmod -R 755 /var/www/html/linkedin-scraper