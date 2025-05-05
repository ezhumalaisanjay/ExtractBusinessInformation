#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Running pre-deploy hook..."

# Set default region if not set
if [ -z "$AWS_REGION" ]; then
    echo "Warning: AWS_REGION is not set. Defaulting to 'us-east-1'."
    AWS_REGION="us-east-1"
fi

# Set default environment if not set
if [ -z "$AMPLIFY_ENV" ]; then
    echo "Warning: AMPLIFY_ENV is not set. Defaulting to 'main'."
    AMPLIFY_ENV="main"
fi

# Example: Perform any pre-deployment tasks
echo "Preparing deployment for environment: $AMPLIFY_ENV in region: $AWS_REGION"

# Add your custom pre-deployment logic here
# For example, validating configuration files or setting up dependencies

echo "Pre-deploy hook completed successfully."
