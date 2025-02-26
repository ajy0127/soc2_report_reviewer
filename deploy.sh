#!/bin/bash
# Deployment script for the SOC2 Report Reviewer application

set -e

# Default values
STACK_NAME="soc2-report-reviewer"
ENVIRONMENT="dev"
NOTIFICATION_EMAIL="admin@example.com"
S3_BUCKET=""
REGION="us-east-1"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --stack-name)
      STACK_NAME="$2"
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
    --s3-bucket)
      S3_BUCKET="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --stack-name NAME       CloudFormation stack name (default: soc2-report-reviewer)"
      echo "  --environment ENV       Deployment environment (default: dev)"
      echo "  --email EMAIL           Notification email (default: admin@example.com)"
      echo "  --s3-bucket BUCKET      S3 bucket for CloudFormation template (required)"
      echo "  --region REGION         AWS region (default: us-east-1)"
      echo "  --help                  Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$S3_BUCKET" ]; then
  echo "Error: S3 bucket is required. Use --s3-bucket to specify."
  exit 1
fi

# Set AWS region
export AWS_DEFAULT_REGION=$REGION

echo "=== SOC2 Report Reviewer Deployment ==="
echo "Stack name: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Notification email: $NOTIFICATION_EMAIL"
echo "S3 bucket: $S3_BUCKET"
echo "Region: $REGION"
echo "======================================="

# Create a deployment package
echo "Creating deployment package..."
mkdir -p .build
cd lambda_package
pip install -r requirements.txt -t .
cd ..
zip -r .build/lambda_package.zip lambda_package

# Upload the deployment package to S3
echo "Uploading deployment package to S3..."
aws s3 cp .build/lambda_package.zip s3://$S3_BUCKET/lambda_package.zip

# Package the CloudFormation template
echo "Packaging CloudFormation template..."
aws cloudformation package \
  --template-file template.yaml \
  --s3-bucket $S3_BUCKET \
  --s3-prefix cloudformation \
  --output-template-file .build/packaged-template.yaml

# Deploy the CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file .build/packaged-template.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    Environment=$ENVIRONMENT \
    NotificationEmail=$NOTIFICATION_EMAIL \
  --capabilities CAPABILITY_IAM

# Get the outputs
echo "Deployment complete. Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs" \
  --output table

echo "Deployment successful!" 