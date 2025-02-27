#!/bin/bash

# SOC2-Analyzer Local Test Runner Script
# This script runs the local testing script for the SOC2-Analyzer project

set -e  # Exit immediately if a command exits with a non-zero status

# Default configuration
PYTHON="python3"
VENV_DIR=".venv"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
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

# Install additional dependencies for local testing
echo "Installing additional dependencies for local testing..."
pip install PyPDF2

# Run the local testing script
echo "Running local tests on SOC2 reports..."
python scripts/test_local.py

# Deactivate virtual environment
deactivate

echo "Local testing completed!"
echo "Check the 'results' directory for analysis outputs." 