#!/bin/bash
# Pre-deployment hook for AWS Amplify
# This script sets up the environment before deployment

echo "Running pre-deployment tasks for LinkedIn Business Intelligence Extractor"

# Create necessary directories
echo "Creating static directories"
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images

# Check Python version
echo "Python version:"
python --version

# Set up virtual environment (if needed)
echo "Setting up Flask application environment"
export FLASK_APP=main.py
export FLASK_ENV=production
export PYTHONPATH=/var/app/current

# Create environmental vars file
echo "Creating .env file"
echo "FLASK_APP=main.py" > .env
echo "FLASK_ENV=production" >> .env
echo "PORT=8080" >> .env

echo "Pre-deployment tasks completed"