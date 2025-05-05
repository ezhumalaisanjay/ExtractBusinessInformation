#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running pre-deploy hook..."

# Example: Check if required environment variables are set
if [ -z "$AWS_REGION" ]; then
    echo "Error: AWS_REGION is not set."
    exit 1
fi

if [ -z "$AMPLIFY_ENV" ]; then
    echo "Error: AMPLIFY_ENV is not set."
    exit 1
fi

# Example: Perform any pre-deployment tasks
echo "Preparing deployment for environment: $AMPLIFY_ENV in region: $AWS_REGION"

# Add your custom pre-deployment logic here
# For example, validating configuration files or setting up dependencies

echo "Pre-deploy hook completed successfully."