#!/bin/bash

# SOC2-Analyzer Deployment Script with Lambda Layer
# This script packages and deploys the SOC2-Analyzer CloudFormation stack
# using a Lambda Layer for binary dependencies

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration values
STACK_NAME="soc2-analyzer"  # Name of the CloudFormation stack
TEMPLATE_FILE="templates/template.yaml"  # Path to the CloudFormation template
S3_BUCKET=""  # Optional: S3 bucket for CloudFormation artifacts
REGION="us-east-1"  # Default AWS region
PROFILE="sandbox"  # AWS CLI profile to use
ENVIRONMENT="dev"  # Environment (dev, test, prod)
NOTIFICATION_EMAIL="alexanderjyawn@gmail.com"  # Email for notifications
LAYER_NAME="soc2-analyzer-dependencies"  # Name of the Lambda Layer

# Parse command line arguments
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
    --layer-name)
      LAYER_NAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display deployment configuration
echo "=== SOC2-Analyzer Deployment with Lambda Layer ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Environment: $ENVIRONMENT"
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "Layer Name: $LAYER_NAME"
echo "============================================="

# Step 1: Create the Lambda Layer with binary dependencies
echo "Creating Lambda Layer for binary dependencies..."
./scripts/layer/create_layer.sh \
  --layer-name "$LAYER_NAME" \
  --region "$REGION" \
  --profile "$PROFILE"

# Get the latest layer version
echo "Getting latest Lambda Layer version..."
LAYER_VERSION=$(aws lambda list-layer-versions \
  --layer-name "$LAYER_NAME" \
  --query "LayerVersions[0].Version" \
  --output text \
  --region "$REGION" \
  --profile "$PROFILE")

LAYER_ARN="arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text --profile $PROFILE):layer:$LAYER_NAME:$LAYER_VERSION"
echo "Using Lambda Layer: $LAYER_ARN"

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Package the Lambda function (without binary dependencies)
echo "Packaging Lambda function..."
mkdir -p "$TEMP_DIR/lambda"
cp -r src/lambda/* "$TEMP_DIR/lambda/"

# Create a modified requirements file without binary dependencies
echo "Creating modified requirements file without binary dependencies..."
grep -v "pymupdf\|ocrmypdf" "$TEMP_DIR/lambda/requirements.txt" > "$TEMP_DIR/lambda/requirements_no_binary.txt"
mv "$TEMP_DIR/lambda/requirements_no_binary.txt" "$TEMP_DIR/lambda/requirements.txt"

# Install non-binary dependencies
echo "Installing non-binary dependencies..."
python3 -m pip install -r "$TEMP_DIR/lambda/requirements.txt" -t "$TEMP_DIR/lambda/" --no-cache-dir

# Create deployment package
echo "Creating deployment package..."
cd "$TEMP_DIR/lambda"
zip -r "$TEMP_DIR/lambda_package.zip" .
cd -

# Deploy using CloudFormation
echo "Deploying CloudFormation stack..."

# Determine deployment command based on whether S3 bucket is provided
if [ -z "$S3_BUCKET" ]; then
  # Deploy without S3 bucket (using local template)
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

# Update Lambda function configuration to use the Layer
echo "Updating Lambda function configuration to use the Lambda Layer..."
aws lambda update-function-configuration \
  --function-name "$FUNCTION_NAME" \
  --layers "$LAYER_ARN" \
  --region "$REGION" \
  --profile "$PROFILE"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

# Display stack outputs
echo "Deployment completed successfully!"
echo "Stack outputs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output table \
  --region "$REGION" \
  --profile "$PROFILE" 