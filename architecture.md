# SOC2 Report Reviewer - Clean Architecture

## Overview

The SOC2 Report Reviewer is a serverless application that analyzes SOC2 reports uploaded to an S3 bucket. The application extracts text from the reports using Amazon Textract, analyzes the content using Amazon Bedrock, and provides a summary of the findings.

## Architecture

The application follows a modular, event-driven architecture with the following components:

1. **S3 Bucket**: Stores SOC2 reports and analysis results
2. **Lambda Function**: Processes S3 events and orchestrates the analysis workflow
3. **Amazon Textract**: Extracts text from PDF reports
4. **Amazon Bedrock**: Analyzes the extracted text
5. **Amazon SES**: Sends email notifications with analysis results

## Component Design

### 1. Core Lambda Handler

The core Lambda handler is responsible for:
- Processing S3 events
- Validating input
- Orchestrating the workflow
- Handling errors
- Returning responses

### 2. Service Modules

Each service is encapsulated in its own module:

- **S3Service**: Handles S3 operations (get object, put object, etc.)
- **TextractService**: Handles text extraction from PDFs
- **BedrockService**: Handles text analysis
- **SESService**: Handles email notifications

### 3. Utility Modules

Utility modules provide common functionality:

- **Validation**: Input validation
- **Error Handling**: Standardized error handling
- **Logging**: Consistent logging

## Error Handling Strategy

1. **Service-Specific Errors**: Each service module defines its own error types
2. **Centralized Error Handler**: A central error handler processes all errors
3. **Detailed Logging**: All errors are logged with context for debugging
4. **Graceful Degradation**: The system can continue processing in "YOLO mode" despite certain errors

## Testing Strategy

1. **Local Testing**: Each module can be tested locally with mock inputs
2. **Integration Testing**: End-to-end testing with real AWS services
3. **Deployment Testing**: Automated tests after deployment

## IAM Permissions

IAM permissions are defined in CloudFormation templates with the principle of least privilege:

1. **Lambda Execution Role**: Permissions for the Lambda function
2. **S3 Bucket Policies**: Permissions for S3 buckets
3. **Cross-Service Permissions**: Permissions for Textract, Bedrock, and SES

## Deployment Process

1. **CloudFormation Template**: Defines all AWS resources
2. **Deployment Script**: Automates the deployment process
3. **Validation**: Validates the deployment

## Monitoring and Debugging

1. **CloudWatch Logs**: All Lambda function logs
2. **CloudWatch Metrics**: Performance metrics
3. **X-Ray Tracing**: Distributed tracing for request flows 