# SOC2 Report Analyzer Deployment Guide

This guide provides step-by-step instructions for deploying the SOC2 Report Analyzer in your AWS environment. It's designed to be accessible for GRC professionals who may not have extensive technical experience.

## Prerequisites

Before you begin, ensure you have the following:

1. **AWS Account**: You'll need an AWS account. If you don't have one, you can create one at [aws.amazon.com](https://aws.amazon.com/).
2. **AWS CLI**: The AWS Command Line Interface should be installed on your computer. [Installation instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
3. **Python 3.9+**: Ensure Python 3.9 or later is installed on your system. [Download Python](https://www.python.org/downloads/).
4. **Git**: You'll need Git to clone the repository. [Download Git](https://git-scm.com/downloads).

## Step 1: Configure AWS CLI

1. Open a terminal or command prompt.
2. Run the following command:
   ```
   aws configure --profile sandbox
   ```
3. Enter your AWS Access Key ID and Secret Access Key when prompted.
4. Set the default region to `us-east-1` or your preferred region.
5. Set the default output format to `json`.

## Step 2: Clone the Repository

1. Open a terminal or command prompt.
2. Navigate to the directory where you want to clone the repository.
3. Run the following command:
   ```
   git clone https://github.com/yourusername/SOC2_report_reviewer.git
   cd SOC2_report_reviewer
   ```

## Step 3: Deploy the Solution

1. Make the deployment script executable:
   ```
   chmod +x scripts/deploy.sh
   ```

2. Run the deployment script:
   ```
   ./scripts/deploy.sh --profile sandbox --region us-east-1
   ```

   You can customize the deployment with the following options:
   - `--stack-name`: Name for the CloudFormation stack (default: soc2-analyzer)
   - `--region`: AWS region to deploy to (default: us-east-1)
   - `--profile`: AWS CLI profile to use (default: sandbox)
   - `--environment`: Environment name (dev, test, prod) (default: dev)
   - `--email`: Email address for notifications
   - `--s3-bucket`: S3 bucket for CloudFormation artifacts (optional)

3. The script will:
   - Create a CloudFormation stack in your AWS account
   - Deploy the necessary AWS resources (Lambda, S3, etc.)
   - Configure the services to work together

4. Wait for the deployment to complete. This typically takes 5-10 minutes.

## Step 4: Upload a SOC2 Report for Analysis

1. Sign in to the AWS Management Console.
2. Navigate to the S3 service.
3. Find the input bucket created by the stack (typically named `soc2-analyzer-input-{random-suffix}`).
4. Click the "Upload" button.
5. Select a SOC2 report PDF file from your computer.
6. Click "Upload" to start the upload process.

## Step 5: Monitor the Analysis Process

1. The system will automatically detect the new file and start processing.
2. You can monitor the process in the AWS Lambda console:
   - Navigate to the Lambda service in the AWS Management Console
   - Find the function named `soc2-analyzer-dev` (or with your custom stack name)
   - Click on the "Monitor" tab to see CloudWatch logs and metrics

## Step 6: Review Analysis Results

1. Once processing is complete, you'll receive an email notification.
2. The email will contain:
   - A summary of the analysis
   - Key findings from the SOC2 report
   - A link to the full analysis results in the S3 output bucket

3. Click the link in the email to access the full analysis results.
4. The results are provided in JSON format with structured sections.

## Troubleshooting

### Common Issues

1. **Deployment Fails**: 
   - Ensure you have the necessary AWS permissions
   - Check that the AWS CLI is properly configured
   - Verify that the template file exists at the specified path

2. **Lambda Function Errors**:
   - Check the CloudWatch logs for the Lambda function
   - Ensure the input file is a valid PDF
   - Verify that the Lambda function has the necessary permissions

3. **No Email Notification**:
   - Check that your email address is correctly specified
   - Verify that Amazon SES is properly configured
   - Check the Lambda function logs for email sending errors

### Getting Help

If you encounter issues not covered in this guide, please:
1. Check the project's GitHub repository for known issues
2. Consult the AWS documentation for the specific services involved
3. Reach out to the project maintainers for assistance

## Next Steps

After successfully deploying the SOC2 Report Analyzer, consider:

1. **Customizing the Analysis**: Modify the configuration to focus on specific SOC2 controls
2. **Adding More Reports**: Upload additional SOC2 reports to build a library of analyses
3. **Creating a Dashboard**: Use the analysis results to create a compliance dashboard
4. **Extending the Solution**: Add support for other compliance frameworks

## Resources

- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Amazon Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/) 