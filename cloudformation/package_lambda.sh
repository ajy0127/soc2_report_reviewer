#!/bin/bash
# Script to package Lambda code for deployment with CloudFormation

# Display banner
echo "====================================================="
echo "SOC 2 Report Analysis Tool - Lambda Packaging Script"
echo "====================================================="
echo

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Get parameters from user
read -p "Enter your S3 bucket name for deployment: " BUCKET_NAME
# read -p "Enter prefix for Lambda code (leave empty for none): " PREFIX
read -p "Enter AWS region (e.g., us-east-1): " REGION

# Set default region if not provided
if [ -z "$REGION" ]; then
    REGION="us-east-1"
    echo "Using default region: $REGION"
fi

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "Creating temporary directory: $TEMP_DIR"

# Copy Lambda code to temporary directory
echo "Copying Lambda code..."
cp -r ../lambda_code/* $TEMP_DIR/

# Install dependencies
echo "Installing dependencies..."
pip install -r ../lambda_code/requirements.txt -t $TEMP_DIR/ --no-cache-dir

# Create ZIP file
echo "Creating ZIP file..."
cd $TEMP_DIR
zip -r ../lambda_code.zip .
cd -
mv $TEMP_DIR/../lambda_code.zip .

# Clean up temporary directory
echo "Cleaning up..."
rm -rf $TEMP_DIR

# Provide instructions for manual upload
cat <<EOL

=====================================================
Lambda code has been packaged into lambda_code.zip.

To upload manually, use one of the following methods:

AWS CLI:
aws s3 cp lambda_code.zip s3://<your-bucket-name>/lambda_code.zip --region <your-region>

AWS Management Console:
1. Navigate to the S3 service.
2. Select your bucket.
3. Click 'Upload' and add the lambda_code.zip file.

=====================================================
EOL

# Keep the local zip file
echo "The Lambda deployment package is also available locally as: lambda_code.zip" 