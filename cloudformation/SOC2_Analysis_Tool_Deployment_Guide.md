# SOC 2 Report Analysis Tool - Printable Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the SOC 2 Report Analysis Tool in your AWS environment. The tool automatically analyzes SOC 2 reports and sends the results to your email. It uses Amazon EventBridge to detect when new PDF files are uploaded to the S3 bucket, triggering the analysis process.

## Before You Begin

You will need:
- An AWS account with administrator access
- A verified email address in Amazon SES (where results will be sent)
- The CloudFormation template file (`soc2-analysis-stack.yaml`)
- The Lambda code package (`lambda_code.zip`)

## Deployment Steps

### Step 0: Package the Lambda Code

Before uploading the Lambda code to S3, you need to package it:

1. Open a terminal and navigate to the `cloudformation` directory.
2. Run the following commands to make the script executable and package the code:
   ```bash
   chmod +x package_lambda.sh
   ./package_lambda.sh
   ```
3. This will create a `lambda_code.zip` file in the `cloudformation` directory, ready for upload.

### Step 1: Upload the Lambda Code Package

1. Sign in to the AWS Management Console
2. Search for "S3" in the search bar and select it
3. Click "Create bucket"
4. Enter a unique bucket name (e.g., "soc2-deployment-[your-name]")
5. Keep all default settings and click "Create bucket"
6. Click on your new bucket name
7. Click "Upload"
8. Click "Add files" and select the `lambda_code.zip` file
9. Click "Upload"
10. Note the bucket name for later use

### Step 2: Deploy the CloudFormation Stack

1. In the AWS Management Console, search for "CloudFormation" and select it
2. Click "Create stack" > "With new resources (standard)"
3. Select "Upload a template file"
4. Click "Choose file" and select the `soc2-analysis-stack.yaml` file
5. Click "Next"
6. Enter a stack name (e.g., "SOC2-Analysis-Tool")
7. Fill in the parameters:
   - **StakeholderEmail**: Your email address
   - **LogLevel**: Leave as "INFO" (default)
   - **BedrockModelId**: Leave as default
   - **DeploymentBucket**: Enter the S3 bucket name from Step 1
   - **DeploymentPrefix**: Leave empty if the Lambda code is at the root of the bucket. Only specify a value if you uploaded the Lambda code to a specific folder in the bucket (without leading or trailing slashes).
8. Click "Next"
9. On the "Configure stack options" page, click "Next"
10. Review the details and check the acknowledgment box at the bottom
11. Click "Create stack"
12. Wait for the stack creation to complete (status: "CREATE_COMPLETE")

### Step 3: Get the S3 Bucket Information

1. Once the stack is created, click on the "Outputs" tab
2. Find the "ReportsBucketName" and "UploadPath" values
3. Note these values for uploading reports

### Step 4: Upload a SOC 2 Report for Analysis

1. In the AWS Management Console, search for "S3" and select it
2. Click on the bucket name shown in the "ReportsBucketName" output
3. Navigate to the "reports/" folder (create it if it doesn't exist)
4. Click "Upload"
5. Click "Add files" and select your SOC 2 report PDF
6. Click "Upload"
7. The analysis will start automatically
8. Check your email for results (usually within 5-10 minutes)

## Troubleshooting

### Email Not Received
- Check your spam/junk folder
- Verify the email address is correct and verified in SES
- Wait up to 15 minutes for processing of large reports

### Upload Issues
- Ensure you're uploading to the correct S3 bucket and "reports/" folder
- Verify the file is a valid PDF
- Check that the file size is under 50MB

### EventBridge Not Triggering
- Verify that EventBridge is enabled for the S3 bucket
- Check that the PDF file was uploaded to the "reports/" folder
- Ensure the file has a ".pdf" extension

### Deployment Failures
- Check the "Events" tab in CloudFormation for error messages
- Verify you have sufficient permissions in your AWS account
- Ensure the Lambda code package is correctly uploaded to S3

## Contact Information

For additional assistance, please contact your IT support team or the tool administrator.

---

*This guide is intended for GRC professionals deploying the SOC 2 Report Analysis Tool. For advanced configuration or customization, please refer to the technical documentation.* 