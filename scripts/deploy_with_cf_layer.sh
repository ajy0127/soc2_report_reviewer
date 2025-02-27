#!/bin/bash

# SOC2-Analyzer Deployment Script with CloudFormation-managed Lambda Layer
# This script builds and uploads a Lambda Layer package, then deploys the CloudFormation stack

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration values
STACK_NAME="soc2-analyzer"  # Name of the CloudFormation stack
TEMPLATE_FILE="templates/template.yaml"  # Path to the CloudFormation template
S3_BUCKET=""  # S3 bucket for CloudFormation artifacts and Layer package
REGION="us-east-1"  # Default AWS region
PROFILE="sandbox"  # AWS CLI profile to use
ENVIRONMENT="dev"  # Environment (dev, test, prod)
NOTIFICATION_EMAIL="alexanderjyawn@gmail.com"  # Email for notifications
LAYER_NAME="soc2-analyzer-dependencies"  # Name of the Lambda Layer
SKIP_LAYER=false  # Whether to skip creating a Lambda Layer

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
    --skip-layer)
      SKIP_LAYER=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display deployment configuration
echo "=== SOC2-Analyzer Deployment with CloudFormation Layer ==="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Environment: $ENVIRONMENT"
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "Skip Layer Creation: $SKIP_LAYER"
echo "=================================================="

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Set default S3 bucket if not provided
if [ -z "$S3_BUCKET" ]; then
  S3_BUCKET="${STACK_NAME}-${ENVIRONMENT}-deployment-${REGION}"
  echo "Creating S3 bucket for deployment artifacts: $S3_BUCKET"
  aws s3 mb "s3://$S3_BUCKET" --region "$REGION" --profile "$PROFILE" || true
fi

LAYER_PACKAGE_KEY=""

if [ "$SKIP_LAYER" = false ]; then
  # Create the Lambda Layer package
  echo "Creating Lambda Layer package..."
  
  # Create the layer structure
  mkdir -p "$TEMP_DIR/python"
  
  # Create a requirements file for the binary dependencies
  cat > "$TEMP_DIR/requirements.txt" << EOF
pymupdf>=1.24.0
ocrmypdf>=15.4.0
EOF
  
  # Check if Docker is installed
  if ! command -v docker &> /dev/null; then
    echo "Docker is not installed or not in PATH. Docker is required for building binary dependencies."
    exit 1
  fi
  
  # Create a Dockerfile for building dependencies
  cat > "$TEMP_DIR/Dockerfile" << EOF
FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt .
RUN pip install -r requirements.txt --target /var/task/python

CMD ["echo", "Dependencies installed successfully"]
EOF
  
  # Build the Docker image and copy dependencies
  echo "Building Docker image for Lambda Layer dependencies..."
  docker build -t soc2-analyzer-layer "$TEMP_DIR" || { echo "Docker build failed"; exit 1; }
  
  # Run a container to extract the dependencies
  echo "Extracting dependencies from Docker container..."
  CONTAINER_ID=$(docker create soc2-analyzer-layer)
  docker cp $CONTAINER_ID:/var/task/. "$TEMP_DIR/"
  docker rm $CONTAINER_ID
  
  # Clean up Docker image
  docker rmi soc2-analyzer-layer
  
  # Create the layer zip file
  echo "Creating Lambda Layer zip file..."
  cd "$TEMP_DIR"
  zip -r "lambda_layer.zip" python
  cd -
  
  # Upload the layer to S3
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  LAYER_PACKAGE_KEY="lambda-layers/${LAYER_NAME}-${ENVIRONMENT}-${TIMESTAMP}.zip"
  echo "Uploading Lambda Layer package to s3://${S3_BUCKET}/${LAYER_PACKAGE_KEY}..."
  aws s3 cp "$TEMP_DIR/lambda_layer.zip" "s3://${S3_BUCKET}/${LAYER_PACKAGE_KEY}" \
    --region "$REGION" \
    --profile "$PROFILE"
fi

# Package the Lambda function (excluding binary dependencies)
echo "Packaging Lambda function..."
mkdir -p "$TEMP_DIR/lambda"
cp -r src/lambda/* "$TEMP_DIR/lambda/"

# If creating a layer, remove binary dependencies from the main package
if [ "$SKIP_LAYER" = false ]; then
  echo "Creating modified requirements file without binary dependencies..."
  grep -v "pymupdf\|ocrmypdf" "$TEMP_DIR/lambda/requirements.txt" > "$TEMP_DIR/lambda/requirements_no_binary.txt"
  mv "$TEMP_DIR/lambda/requirements_no_binary.txt" "$TEMP_DIR/lambda/requirements.txt"
fi

# Install dependencies locally
echo "Installing Lambda function dependencies..."
python3 -m pip install -r "$TEMP_DIR/lambda/requirements.txt" -t "$TEMP_DIR/lambda/" --no-cache-dir

# Create deployment package
echo "Creating Lambda function deployment package..."
cd "$TEMP_DIR/lambda"
zip -r "$TEMP_DIR/lambda_package.zip" .
cd -

# Upload the Lambda package to S3
LAMBDA_PACKAGE_KEY="lambda-packages/soc2-analyzer-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S).zip"
echo "Uploading Lambda function package to s3://${S3_BUCKET}/${LAMBDA_PACKAGE_KEY}..."
aws s3 cp "$TEMP_DIR/lambda_package.zip" "s3://${S3_BUCKET}/${LAMBDA_PACKAGE_KEY}" \
  --region "$REGION" \
  --profile "$PROFILE"

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file "$TEMPLATE_FILE" \
  --stack-name "$STACK_NAME" \
  --parameter-overrides \
    Environment="$ENVIRONMENT" \
    NotificationEmail="$NOTIFICATION_EMAIL" \
    LayerPackageBucket="$S3_BUCKET" \
    LayerPackageKey="$LAYER_PACKAGE_KEY" \
  --capabilities CAPABILITY_IAM \
  --region "$REGION" \
  --profile "$PROFILE"

# Update Lambda function code from S3
echo "Updating Lambda function code..."
FUNCTION_NAME="${STACK_NAME}-${ENVIRONMENT}"
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --s3-bucket "$S3_BUCKET" \
  --s3-key "$LAMBDA_PACKAGE_KEY" \
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