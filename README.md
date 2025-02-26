[![CI](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci.yml)

# SOC 2 Report Analysis Tool

An automated serverless solution for analyzing SOC 2 reports using AWS services and AI, designed for GRC professionals.

## Overview

The SOC 2 Report Analysis Tool is designed to streamline the process of reviewing and analyzing SOC 2 reports. It leverages AWS services to automatically extract text from PDF reports, analyze the content using AI, identify key controls, map them to industry frameworks, and deliver insights to stakeholders via email.

## Key Features

- **Automated PDF Processing**: Automatically processes SOC 2 reports when uploaded to an S3 bucket
- **AI-Powered Analysis**: Uses Amazon Bedrock to analyze report content and extract key information
- **Framework Mapping**: Maps controls to CIS Top 20 and OWASP Top 10 frameworks
- **Gap Identification**: Identifies potential gaps in security controls
- **Quality Rating**: Provides a standardized quality rating for reports
- **Email Notifications**: Delivers analysis results directly to stakeholders via email
- **Report Tagging**: Tags processed reports with analysis date for tracking

## Architecture

The solution uses the following AWS services:

- **Amazon S3**: Stores SOC 2 reports and analysis results
- **AWS Lambda**: Processes reports and orchestrates the analysis workflow
- **Amazon Textract**: Extracts text from PDF reports
- **Amazon Bedrock**: Analyzes report content using AI
- **Amazon SES**: Sends email notifications with analysis results

## Workflow

1. User uploads a SOC 2 report (PDF) to the designated S3 bucket
2. S3 event triggers the Lambda function
3. Lambda validates that the file is a PDF
4. Textract extracts text from the PDF
5. Bedrock analyzes the extracted text
6. Analysis results are stored as JSON in the S3 bucket
7. An HTML email with the analysis is sent to stakeholders
8. The original PDF is tagged with the analysis date

## Getting Started

### Prerequisites

- AWS Account with access to required services
- Access to the AWS Management Console
- A verified email address in Amazon SES (for sending notifications)

### Next Steps

For detailed deployment instructions, please refer to the [CloudFormation Deployment Guide](cloudformation/SOC2_Analysis_Tool_Deployment_Guide.md). This guide will walk you through the entire deployment process, including packaging the Lambda code and setting up the necessary AWS resources.

## Testing

The project includes comprehensive tests to ensure the quality and correctness of the code:

### Running Tests

To run all tests, use the provided test script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

This script will:
1. Check for and install required dependencies (pytest, pytest-mock, cfn-lint)
2. Validate the CloudFormation template using cfn-lint
3. Run all unit tests using pytest

### Test Coverage

The tests cover:
- **Validation Utilities**: Tests for input validation functions
- **Lambda Handler**: Tests for the main Lambda function handler
- **Textract Service**: Tests for text extraction from PDFs
- **Bedrock Service**: Tests for AI analysis of report content
- **Error Handling**: Tests for proper error handling and retries

### CloudFormation Validation

The CloudFormation template is validated using cfn-lint to ensure it follows best practices and will deploy successfully. You can run this validation separately:

```bash
cd cloudformation
chmod +x validate_template.sh
./validate_template.sh
```

## Project Structure

```
.
├── PRD.md                     # Product Requirements Document
├── implementation_plan.md     # Implementation Plan
├── README.md                  # This file
├── run_tests.sh               # Script to run all tests
├── cloudformation/            # CloudFormation deployment
│   ├── README.md              # Deployment guide
│   ├── soc2-analysis-stack.yaml # CloudFormation template
│   ├── package_lambda.sh      # Script to package Lambda code
│   ├── validate_template.sh   # Script to validate the template
│   ├── lint_template.sh       # Script to lint the template
│   ├── pre_deployment_checklist.md # Checklist before deployment
│   ├── SOC2_Analysis_Tool_Deployment_Guide.md # Printable guide
│   ├── generate_pdf_guide.py  # Script to generate PDF guide
│   └── faq.md                 # Frequently Asked Questions
├── lambda_code/               # Lambda function code
│   ├── app.py                 # Main Lambda handler
│   ├── textract_service.py    # Textract integration
│   ├── bedrock_service.py     # Bedrock integration
│   ├── utils/                 # Utility functions
│   └── templates/             # Email templates
└── tests/                     # Test files
    ├── conftest.py            # Pytest configuration
    ├── test_validation.py     # Tests for validation utilities
    ├── test_lambda_handler.py # Tests for Lambda handler
    ├── test_textract_service.py # Tests for Textract service
    └── test_bedrock_service.py # Tests for Bedrock service
```

## Configuration

The following parameters can be configured during deployment:

- **StakeholderEmail**: Email address to send analysis results to
- **LogLevel**: Logging level for the Lambda function (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **BedrockModelId**: Amazon Bedrock model ID to use for analysis

## Cost Estimation

The estimated cost per report analysis (75-page report) is approximately $0.33, including:
- Textract: ~$0.11
- Bedrock: ~$0.21
- Lambda: ~$0.005
- SES & S3: negligible

## Security Considerations

- All data is encrypted at rest using SSE-S3
- All data transfers use HTTPS (TLS)
- IAM roles follow the principle of least privilege
- No sensitive data is included in object tags

## Troubleshooting

If you encounter any issues:

1. Check the [CloudFormation Deployment Guide](cloudformation/README.md) for troubleshooting tips
2. Review the [Frequently Asked Questions](cloudformation/faq.md)
3. Verify that the email address is correct and check your spam folder
4. Ensure you're uploading PDF files to the correct S3 path

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
