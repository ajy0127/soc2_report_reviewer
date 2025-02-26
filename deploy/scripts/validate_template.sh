#!/bin/bash
# Script to validate the CloudFormation template

# Display banner
echo "====================================================="
echo "SOC 2 Report Analysis Tool - Template Validation"
echo "====================================================="
echo

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Get AWS region
read -p "Enter AWS region (e.g., us-east-1) or press Enter for default: " REGION

# Set default region if not provided
if [ -z "$REGION" ]; then
    REGION="us-east-1"
    echo "Using default region: $REGION"
fi

# Validate the template
echo "Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://soc2-analysis-stack.yaml \
    --region $REGION

# Check if validation was successful
if [ $? -eq 0 ]; then
    echo
    echo "====================================================="
    echo "Success! The CloudFormation template is valid."
    echo "====================================================="
else
    echo
    echo "====================================================="
    echo "Error: The CloudFormation template is not valid."
    echo "Please fix the issues and try again."
    echo "====================================================="
fi 