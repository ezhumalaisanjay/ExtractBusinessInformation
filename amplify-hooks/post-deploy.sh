#!/bin/bash
# Post-deployment hook for AWS Amplify
# This script runs after deployment to check if everything is up and running

echo "Running post-deployment checks for LinkedIn Business Intelligence Extractor"

# Initialize application context
echo "Initializing Flask application context"
python -c "from main import app; print('Flask app initialized successfully')"

# Verify CORS handler is available
echo "Verifying CORS handler"
if [ -f "scripts/cors-handler.py" ]; then
    echo "CORS handler found"
    python -c "import scripts.cors_handler; print('CORS handler imported successfully')"
else
    echo "Warning: CORS handler not found. CORS support may be unavailable."
fi

# Check if the health endpoint is working
echo "Checking health endpoint"
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "Health endpoint is working"
else
    echo "Warning: Health endpoint may not be working properly"
fi

echo "Post-deployment checks completed"