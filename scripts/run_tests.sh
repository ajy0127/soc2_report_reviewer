#!/bin/bash

# SOC2-Analyzer Test Runner Script
# This script sets up and runs tests for the SOC2-Analyzer project

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration
PYTHON="python3"
VENV_DIR=".venv"
COVERAGE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --coverage)
      COVERAGE=true
      shift
      ;;
    --python)
      PYTHON="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv $VENV_DIR
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Run tests
echo "Running tests..."
if [ "$COVERAGE" = true ]; then
  # Run tests with coverage
  echo "Running tests with coverage..."
  coverage run -m pytest
  coverage report -m
  coverage html
  echo "Coverage report generated in htmlcov/"
else
  # Run tests without coverage
  pytest
fi

# Deactivate virtual environment
deactivate

echo "Tests completed!" 