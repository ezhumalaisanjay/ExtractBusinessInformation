#!/bin/bash

# Check if the PID file exists
if [ -f /var/www/html/linkedin-scraper/gunicorn.pid ]; then
    # Get the PID
    PID=$(cat /var/www/html/linkedin-scraper/gunicorn.pid)
    
    # Check if the process is running
    if ps -p $PID > /dev/null; then
        echo "Stopping application..."
        kill $PID
        
        # Wait for the process to terminate
        sleep 5
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Force stopping application..."
            kill -9 $PID
        fi
    else
        echo "Application is not running"
    fi
    
    # Remove the PID file
    rm -f /var/www/html/linkedin-scraper/gunicorn.pid
else
    echo "PID file not found, attempting to find and kill gunicorn processes"
    pkill -f gunicorn
fi