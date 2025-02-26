#!/bin/bash
# Script to lint the CloudFormation template using cfn-lint

# Display banner
echo "====================================================="
echo "SOC 2 Report Analysis Tool - Template Linting"
echo "====================================================="
echo

# Check if cfn-lint is installed
if ! command -v cfn-lint &> /dev/null; then
    echo "Error: cfn-lint is not installed. Installing it now..."
    pip install cfn-lint
    
    # Check if installation was successful
    if ! command -v cfn-lint &> /dev/null; then
        echo "Failed to install cfn-lint. Please install it manually:"
        echo "pip install cfn-lint"
        exit 1
    fi
    
    echo "cfn-lint installed successfully."
fi

# Run cfn-lint on the template
echo "Linting CloudFormation template..."
cfn-lint soc2-analysis-stack.yaml

# Check if linting was successful
if [ $? -eq 0 ]; then
    echo
    echo "====================================================="
    echo "Success! The CloudFormation template passed linting."
    echo "====================================================="
else
    echo
    echo "====================================================="
    echo "Warning: The CloudFormation template has linting issues."
    echo "Please review the issues above and fix them if necessary."
    echo "====================================================="
    exit 1
fi 