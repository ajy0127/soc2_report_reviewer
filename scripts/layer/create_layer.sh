#!/bin/bash

# SOC2-Analyzer Lambda Layer Creation Script
# This script creates a Lambda Layer with the binary dependencies

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration values
LAYER_NAME="soc2-analyzer-dependencies"
REGION="us-east-1"
PROFILE="sandbox"
RUNTIME="python3.9"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --layer-name)
      LAYER_NAME="$2"
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
    --runtime)
      RUNTIME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Display configuration
echo "=== Lambda Layer Creation ==="
echo "Layer Name: $LAYER_NAME"
echo "Region: $REGION"
echo "Profile: $PROFILE"
echo "Runtime: $RUNTIME"
echo "==========================="

# Create a temporary directory for layer packaging
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

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

# Create or update the Lambda Layer
echo "Publishing Lambda Layer..."
LAYER_VERSION=$(aws lambda publish-layer-version \
  --layer-name "$LAYER_NAME" \
  --description "SOC2 Analyzer binary dependencies" \
  --zip-file "fileb://$TEMP_DIR/lambda_layer.zip" \
  --compatible-runtimes "$RUNTIME" \
  --region "$REGION" \
  --profile "$PROFILE" \
  --query "Version" \
  --output text)

echo "Lambda Layer published successfully. Version: $LAYER_VERSION"
echo "Layer ARN: arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text --profile $PROFILE):layer:$LAYER_NAME:$LAYER_VERSION"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Lambda Layer creation completed!"
echo "=============================="
echo "To modify the SOC2-Analyzer Lambda function to use this layer, run:"
echo "aws lambda update-function-configuration \\"
echo "  --function-name soc2-analyzer-dev \\"
echo "  --layers arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text --profile $PROFILE):layer:$LAYER_NAME:$LAYER_VERSION \\"
echo "  --region $REGION \\"
echo "  --profile $PROFILE"
echo "==============================" 