#!/bin/bash

# SOC2-Analyzer Deployment Script
# This script packages and deploys the SOC2-Analyzer CloudFormation stack

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration values
# These can be overridden with command-line arguments
STACK_NAME="soc2-analyzer"  # Name of the CloudFormation stack
TEMPLATE_FILE="templates/template.yaml"  # Path to the CloudFormation template
S3_BUCKET=""  # Optional: S3 bucket for CloudFormation artifacts
REGION="us-east-1"  # Default AWS region
PROFILE="sandbox"  # AWS CLI profile to use
ENVIRONMENT="dev"  # Environment (dev, test, prod)
NOTIFICATION_EMAIL="alexanderjyawn@gmail.com"  # Email for notifications

# Parse command line arguments
# This allows users to customize the deployment parameters
while [[ $# -gt 0 ]]; do
  case $1 in
    --stack-name)
      STACK_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --s3-bucket)
      S3_BUCKET="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --email)
      NOTIFICATION_EMAIL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display deployment configuration
echo "=== SOC2-Analyzer Deployment ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Environment: $ENVIRONMENT"
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "================================"

# Create a temporary directory for packaging
# This will be used to prepare the Lambda deployment package
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Package the Lambda function
# Copy the source code to the temporary directory
echo "Packaging Lambda function..."
mkdir -p "$TEMP_DIR/lambda"
cp -r src/lambda/* "$TEMP_DIR/lambda/"

# Install dependencies
# This installs the required Python packages into the Lambda package
echo "Installing dependencies..."
python3 -m pip install -r "$TEMP_DIR/lambda/requirements.txt" -t "$TEMP_DIR/lambda/" --no-cache-dir

# Create deployment package
# Zip the Lambda function code and dependencies
echo "Creating deployment package..."
cd "$TEMP_DIR/lambda"
zip -r "$TEMP_DIR/lambda_package.zip" .
cd -

# Deploy using CloudFormation
# This creates or updates the CloudFormation stack
echo "Deploying CloudFormation stack..."

# Determine deployment command based on whether S3 bucket is provided
if [ -z "$S3_BUCKET" ]; then
  # Deploy without S3 bucket (using local template)
  # This is simpler but has template size limitations
  aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
      Environment="$ENVIRONMENT" \
      NotificationEmail="$NOTIFICATION_EMAIL" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION" \
    --profile "$PROFILE"
else
  # Package and deploy using S3 bucket
  # This approach supports larger templates and nested stacks
  aws cloudformation package \
    --template-file "$TEMPLATE_FILE" \
    --s3-bucket "$S3_BUCKET" \
    --output-template-file "$TEMP_DIR/packaged-template.yaml" \
    --region "$REGION" \
    --profile "$PROFILE"
    
  aws cloudformation deploy \
    --template-file "$TEMP_DIR/packaged-template.yaml" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
      Environment="$ENVIRONMENT" \
      NotificationEmail="$NOTIFICATION_EMAIL" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION" \
    --profile "$PROFILE"
fi

# Update Lambda function code
# This updates the Lambda function with our deployment package
# We do this separately to ensure the latest code is deployed
echo "Updating Lambda function code..."
FUNCTION_NAME="${STACK_NAME}-${ENVIRONMENT}"

# Get the package size
PACKAGE_SIZE=$(stat -f%z "$TEMP_DIR/lambda_package.zip")
SIZE_LIMIT=50000000  # 50MB limit for direct upload

if [ $PACKAGE_SIZE -gt $SIZE_LIMIT ]; then
  echo "Package size ($PACKAGE_SIZE bytes) exceeds direct upload limit ($SIZE_LIMIT bytes)"
  echo "Uploading package to S3 first..."
  
  # Create S3 bucket if it doesn't exist and S3_BUCKET is not provided
  if [ -z "$S3_BUCKET" ]; then
    S3_BUCKET="${STACK_NAME}-${ENVIRONMENT}-lambda-packages-${REGION}"
    echo "Creating S3 bucket for Lambda packages: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET" --region "$REGION" --profile "$PROFILE" || true
  fi
  
  # Upload package to S3
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  S3_KEY="lambda-packages/${FUNCTION_NAME}-${TIMESTAMP}.zip"
  echo "Uploading package to s3://${S3_BUCKET}/${S3_KEY}"
  aws s3 cp "$TEMP_DIR/lambda_package.zip" "s3://${S3_BUCKET}/${S3_KEY}" --region "$REGION" --profile "$PROFILE"
  
  # Update Lambda function from S3
  echo "Updating Lambda function from S3..."
  aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --s3-bucket "$S3_BUCKET" \
    --s3-key "$S3_KEY" \
    --region "$REGION" \
    --profile "$PROFILE"
else
  # Direct upload for smaller packages
  echo "Updating Lambda function with direct upload..."
  aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$TEMP_DIR/lambda_package.zip" \
    --region "$REGION" \
    --profile "$PROFILE"
fi

# Clean up
# Remove the temporary directory
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Display stack outputs
# This shows the outputs from the CloudFormation stack
echo "Deployment completed successfully!"
echo "Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output table \
  --region "$REGION" \
  --profile "$PROFILE" 