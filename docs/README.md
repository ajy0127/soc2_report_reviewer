# SOC 2 Report Analysis Tool

A tool for automatically analyzing SOC 2 reports using AWS services.

## Project Structure

```
soc2_report_reviewer/
├── deploy/                    # Deployment files
│   ├── cloudformation/        # CloudFormation templates
│   └── scripts/               # Deployment scripts
├── docs/                      # Documentation
├── src/                       # Source code
│   └── soc2_analyzer/         # Main package
│       ├── core/              # Core functionality
│       ├── services/          # AWS service integrations
│       ├── utils/             # Utility functions
│       └── templates/         # Email templates
├── tests/                     # Test files
├── setup.py                   # Package setup
└── requirements.txt           # Dependencies
```

## Components

### Core Module

Contains the main Lambda handler function that orchestrates the analysis flow.

### Services Module

- `textract_service.py`: Extracts text from PDF files using Amazon Textract
- `bedrock_service.py`: Analyzes text using Amazon Bedrock
- `s3_service.py`: Stores and retrieves data from Amazon S3
- `ses_service.py`: Sends email notifications via Amazon SES

### Utils Module

- `validation.py`: Validates inputs and outputs
- `error_handling.py`: Common error handling utilities
- `logging.py`: Logging utilities

## Getting Started

### Prerequisites

- Python 3.9+
- AWS account with appropriate permissions
- Configured AWS credentials

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```
   pip install -e .
   ```

### Testing

Run tests with:

```
./run_tests.sh
```

## Deployment

See the CloudFormation template in `deploy/cloudformation/` for AWS resource configuration.

Use the provided scripts in `deploy/scripts/` to package and deploy the Lambda function.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 