# SOC2-Analyzer

An automated system for analyzing SOC2 reports using AWS serverless architecture and AI.

## Overview

SOC2-Analyzer automates the process of analyzing SOC2 reports, extracting key information, and providing structured insights. It leverages AWS services including Lambda, S3, Textract, Amazon Bedrock, and SES to create a serverless workflow that processes PDF reports and delivers analysis results via email.

## Key Features

- **Automated Text Extraction**: Uses Amazon Textract to extract text from PDF SOC2 reports
- **AI-Powered Analysis**: Leverages Amazon Bedrock to analyze report content and extract key insights
- **Serverless Architecture**: Fully serverless implementation using AWS Lambda and S3
- **Email Notifications**: Sends analysis results via email using Amazon SES
- **Standardized Output**: Provides structured JSON output with consistent format

## Architecture

The SOC2-Analyzer uses the following AWS services:

- **Amazon S3**: Stores input SOC2 reports and analysis results
- **AWS Lambda**: Processes reports and orchestrates the analysis workflow
- **Amazon Textract**: Extracts text from PDF documents
- **Amazon Bedrock**: Performs AI analysis of report content
- **Amazon SES**: Sends email notifications with analysis results
- **Amazon EventBridge**: Triggers Lambda function when new reports are uploaded
- **Amazon CloudWatch**: Monitors and logs system activity
- **AWS IAM**: Manages permissions and access control

## Deployment

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- Python 3.9 or later
- An AWS account with access to all required services
- A verified email address in Amazon SES for notifications

### Deployment Steps

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/soc2-analyzer.git
   cd soc2-analyzer
   ```

2. Deploy the CloudFormation stack using the provided script:
   ```
   ./scripts/deploy.sh --profile sandbox --region us-east-1
   ```

   Optional parameters:
   - `--stack-name`: Name for the CloudFormation stack (default: soc2-analyzer)
   - `--region`: AWS region to deploy to (default: us-east-1)
   - `--profile`: AWS CLI profile to use (default: sandbox)
   - `--environment`: Environment name (dev, test, prod) (default: dev)
   - `--email`: Email address for notifications (default: alexanderjyawn@gmail.com)
   - `--s3-bucket`: S3 bucket for CloudFormation artifacts (optional)

## Usage

1. **Upload a SOC2 Report**:
   - Navigate to the S3 console and find the input bucket created by the stack
   - Upload a SOC2 report in PDF format

2. **Automated Processing**:
   - The system automatically detects the new file and starts processing
   - Text is extracted using Amazon Textract
   - The content is analyzed using Amazon Bedrock
   - Results are stored in the output S3 bucket

3. **Receive Notification**:
   - Once processing is complete, you'll receive an email notification
   - The email contains a summary of the analysis and a link to the full results

4. **Review Results**:
   - Click the link in the email to access the full analysis results
   - The results are provided in JSON format with structured sections

## Project Structure

```
soc2-analyzer/
├── docs/                   # Documentation
├── scripts/                # Deployment and utility scripts
├── src/                    # Source code
│   └── lambda/             # Lambda function code
│       ├── app.py          # Main Lambda handler
│       ├── services/       # Service modules
│       └── utils/          # Utility modules
├── templates/              # CloudFormation templates
└── tests/                  # Test files
    └── unit/               # Unit tests
```

## Development

### Local Development Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r src/lambda/requirements.txt
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```
   ./scripts/run_tests.sh
   ```

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration:

1. **Automated Testing**: All tests are automatically run on push to main/develop branches and on pull requests
2. **CloudFormation Validation**: The CloudFormation template is validated using cfn-lint
3. **Code Quality Checks**: Linting is performed to ensure code quality

The CI/CD pipeline does not include automatic deployment to AWS. Users should deploy the application manually using the CloudFormation template as described in the Deployment section.

For more details on the CI/CD setup, see the [GitHub Actions documentation](.github/README.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- AWS for providing the cloud infrastructure
- Anthropic for the Claude AI model used in analysis 