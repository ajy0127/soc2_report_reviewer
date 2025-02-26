[![CI](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/ajy0127/soc2_report_reviewer/actions/workflows/ci.yml)

# SOC2 Report Reviewer

A serverless application that analyzes SOC2 reports uploaded to an S3 bucket using Amazon Textract and Amazon Bedrock.

## Architecture

The application follows a modular, event-driven architecture with the following components:

1. **S3 Bucket**: Stores SOC2 reports and analysis results
2. **Lambda Function**: Processes S3 events and orchestrates the analysis workflow
3. **Amazon Textract**: Extracts text from PDF reports
4. **Amazon Bedrock**: Analyzes the extracted text
5. **Amazon SES**: Sends email notifications with analysis results

For more details, see the [architecture document](architecture.md).

## Prerequisites

- AWS CLI installed and configured
- Python 3.9 or later
- An AWS account with appropriate permissions
- An S3 bucket for CloudFormation deployment artifacts

## Deployment

You can deploy the application using the provided deployment script:

```bash
./deploy.sh --s3-bucket YOUR_DEPLOYMENT_BUCKET --email your.email@example.com
```

### Deployment Options

- `--stack-name NAME`: CloudFormation stack name (default: soc2-report-reviewer)
- `--environment ENV`: Deployment environment (default: dev)
- `--email EMAIL`: Notification email (default: admin@example.com)
- `--s3-bucket BUCKET`: S3 bucket for CloudFormation template (required)
- `--region REGION`: AWS region (default: us-east-1)

## Usage

1. Upload a SOC2 report PDF to the `reports/` prefix in the S3 bucket created by the CloudFormation stack.
2. The Lambda function will automatically process the report and generate an analysis.
3. The analysis will be stored in the same S3 bucket with the suffix `_analysis.json`.
4. A notification email will be sent to the specified email address.

## Development

### Project Structure

```
.
├── architecture.md          # Architecture documentation
├── deploy.sh                # Deployment script
├── lambda_package/          # Lambda function code
│   ├── app.py               # Main Lambda handler
│   ├── requirements.txt     # Python dependencies
│   ├── services/            # Service modules
│   │   ├── s3_service.py    # S3 operations
│   │   ├── textract_service.py # Text extraction
│   │   ├── bedrock_service.py # Text analysis
│   │   └── ses_service.py   # Email notifications
│   ├── templates/           # Email templates
│   └── utils/               # Utility modules
│       ├── validation.py    # Input validation
│       ├── error_handling.py # Error handling
│       └── aws_helpers.py   # AWS helper functions
└── template.yaml            # CloudFormation template
```

### Local Testing

You can test the Lambda function locally using the AWS SAM CLI:

```bash
sam local invoke AnalysisFunction -e events/s3-event.json
```

## Troubleshooting

If you encounter issues with the Lambda function, check the CloudWatch Logs for error messages. Common issues include:

- IAM permissions: Make sure the Lambda function has the necessary permissions to access S3, Textract, Bedrock, and SES.
- S3 bucket configuration: Make sure the S3 bucket is properly configured with event notifications.
- PDF format: Make sure the PDF is properly formatted and can be processed by Textract.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
