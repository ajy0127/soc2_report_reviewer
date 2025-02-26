#!/bin/bash
# Script to run tests for the SOC 2 Report Analysis Tool

# Display banner
echo "====================================================="
echo "SOC 2 Report Analysis Tool - Test Runner"
echo "====================================================="
echo

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed. Installing it now..."
    pip install pytest pytest-mock
    
    # Check if installation was successful
    if ! command -v pytest &> /dev/null; then
        echo "Failed to install pytest. Please install it manually:"
        echo "pip install pytest pytest-mock"
        exit 1
    fi
    
    echo "pytest installed successfully."
fi

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

# Run CloudFormation linting
echo
echo "Running CloudFormation linting..."
cfn-lint cloudformation/soc2-analysis-stack.yaml

# Check if linting was successful
if [ $? -eq 0 ]; then
    echo "CloudFormation template passed linting."
else
    echo "CloudFormation template has linting issues. Please fix them before running tests."
    exit 1
fi

# Run pytest
echo
echo "Running pytest..."
pytest tests/ -v

# Check if tests were successful
if [ $? -eq 0 ]; then
    echo
    echo "====================================================="
    echo "Success! All tests passed."
    echo "====================================================="
else
    echo
    echo "====================================================="
    echo "Error: Some tests failed. Please fix the issues and try again."
    echo "====================================================="
    exit 1
fi 