# SOC 2 Report Analysis Tool - Deployment Guide

This guide explains how to deploy the SOC 2 Report Analysis Tool using AWS CloudFormation. The process is designed to be straightforward, even for those without extensive technical experience.

## Prerequisites

1. An AWS account with appropriate permissions
2. The Lambda code package (lambda_code.zip) uploaded to an S3 bucket
3. Access to the AWS Management Console

## Deployment Steps

### Option 1: Using the AWS Management Console (Recommended for GRC Professionals)

1. **Sign in to the AWS Management Console**
   - Go to https://console.aws.amazon.com and sign in with your credentials

2. **Navigate to CloudFormation**
   - In the AWS Management Console, search for "CloudFormation" in the search bar and select it

3. **Create a new stack**
   - Click the "Create stack" button
   - Select "With new resources (standard)"

4. **Specify template**
   - Select "Upload a template file"
   - Click "Choose file" and select the `soc2-analysis-stack.yaml` file from your computer
   - Click "Next"

5. **Specify stack details**
   - Enter a name for your stack (e.g., "SOC2-Analysis-Tool")
   - Fill in the parameters:
     - **StakeholderEmail**: The email address where analysis results will be sent
     - **LogLevel**: The logging level (default: INFO)
     - **BedrockModelId**: The Amazon Bedrock model ID to use (default is provided)
     - **DeploymentBucket**: The S3 bucket where your Lambda code package is stored
     - **DeploymentPrefix**: The path prefix to the Lambda code in the S3 bucket (if any)
   - Click "Next"

6. **Configure stack options**
   - Add any tags if desired (optional)
   - Configure stack options if needed (optional)
   - Click "Next"

7. **Review**
   - Review all the details
   - Check the acknowledgment box at the bottom if AWS CloudFormation displays capabilities notices
   - Click "Create stack"

8. **Wait for deployment**
   - The deployment process will take a few minutes
   - You can monitor the progress in the "Events" tab

### Option 2: Using the AWS CLI

If you're comfortable with the command line, you can deploy using the AWS CLI:

```bash
aws cloudformation create-stack \
  --stack-name SOC2-Analysis-Tool \
  --template-body file://soc2-analysis-stack.yaml \
  --parameters \
      ParameterKey=StakeholderEmail,ParameterValue=your-email@example.com \
      ParameterKey=DeploymentBucket,ParameterValue=your-deployment-bucket \
      ParameterKey=DeploymentPrefix,ParameterValue=your-prefix \
  --capabilities CAPABILITY_IAM
```

## After Deployment

Once deployment is complete:

1. **Note the outputs**
   - In the CloudFormation console, go to the "Outputs" tab of your stack
   - Note the S3 bucket name and upload path for SOC 2 reports

2. **Upload a SOC 2 report**
   - Upload a SOC 2 report PDF to the S3 path shown in the outputs
   - The analysis will start automatically
   - Results will be sent to the email address you specified

## Troubleshooting

If you encounter any issues:

1. **Check CloudWatch Logs**
   - In the AWS Management Console, search for "CloudWatch"
   - Go to "Log groups"
   - Find the log group for your Lambda function (it will be named like `/aws/lambda/SOC2-Analysis-Tool-AnalysisFunction-XXXX`)
   - Review the logs for any errors

2. **Common issues**
   - **Email not received**: Verify that the email address is correct and check your spam folder
   - **Lambda function errors**: Check the CloudWatch logs for details
   - **S3 upload issues**: Ensure you're uploading to the correct path and the file is a valid PDF

## Updating the Stack

If you need to update the deployment:

1. In the CloudFormation console, select your stack
2. Click "Update"
3. Choose "Replace current template" or "Use current template"
4. Follow the prompts to update the stack

## Deleting the Stack

To remove all resources:

1. In the CloudFormation console, select your stack
2. Click "Delete"
3. Confirm the deletion

**Note**: This will delete all resources created by the stack, including the S3 bucket and any reports stored in it. 