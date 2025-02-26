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
read -p "Enter prefix for Lambda code (leave empty for none): " PREFIX
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

# Upload to S3
echo "Uploading to S3..."
if [ -z "$PREFIX" ]; then
    aws s3 cp lambda_code.zip s3://$BUCKET_NAME/lambda_code.zip --region $REGION
else
    aws s3 cp lambda_code.zip s3://$BUCKET_NAME/$PREFIX/lambda_code.zip --region $REGION
fi

# Check if upload was successful
if [ $? -eq 0 ]; then
    echo
    echo "====================================================="
    echo "Success! Lambda code has been packaged and uploaded."
    echo
    echo "Deployment Information:"
    echo "- S3 Bucket: $BUCKET_NAME"
    if [ -z "$PREFIX" ]; then
        echo "- S3 Key: lambda_code.zip"
    else
        echo "- S3 Key: $PREFIX/lambda_code.zip"
    fi
    echo
    echo "When deploying the CloudFormation template, use:"
    echo "- DeploymentBucket: $BUCKET_NAME"
    if [ -z "$PREFIX" ]; then
        echo "- DeploymentPrefix: (leave empty)"
    else
        echo "- DeploymentPrefix: $PREFIX"
    fi
    echo "====================================================="
else
    echo
    echo "Error: Failed to upload Lambda code to S3."
    echo "Please check your AWS credentials and bucket permissions."
    echo
fi

# Keep the local zip file
echo "The Lambda deployment package is also available locally as: lambda_code.zip" 