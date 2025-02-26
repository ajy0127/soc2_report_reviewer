# SOC 2 Report Analysis Tool - Pre-Deployment Checklist

Use this checklist to ensure you have everything ready before deploying the SOC 2 Report Analysis Tool.

## AWS Account Setup

- [ ] I have an AWS account with administrator access
- [ ] I have access to the AWS Management Console
- [ ] I have verified my email address in Amazon SES (in the region where I'll deploy)
- [ ] I have the necessary permissions to create the following resources:
  - S3 buckets
  - Lambda functions
  - IAM roles
  - CloudFormation stacks

## Required Files

- [ ] I have the CloudFormation template file (`soc2-analysis-stack.yaml`)
- [ ] I have the Lambda code package (`lambda_code.zip`)
  - *Note: If you don't have this file, you can create it using the `package_lambda.sh` script*

## Deployment Information

- [ ] I have decided on a name for my CloudFormation stack
- [ ] I have the email address where analysis results should be sent
- [ ] I have created an S3 bucket for storing the Lambda code package
- [ ] I have uploaded the Lambda code package to the S3 bucket

## Post-Deployment Plan

- [ ] I know how to upload SOC 2 reports to the S3 bucket after deployment
- [ ] I understand how to check CloudWatch logs if there are issues
- [ ] I know how to update the stack if needed in the future

## Optional Considerations

- [ ] I have considered the cost implications of using this tool
- [ ] I have reviewed the security considerations in the documentation
- [ ] I have a plan for backing up analysis results if needed

---

Once you've checked all the required items, you're ready to proceed with deployment using the instructions in the Deployment Guide. 