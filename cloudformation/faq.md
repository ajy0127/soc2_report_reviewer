# SOC 2 Report Analysis Tool - Frequently Asked Questions

## General Questions

### What is the SOC 2 Report Analysis Tool?
The SOC 2 Report Analysis Tool is an automated solution that helps GRC professionals analyze SOC 2 reports more efficiently. It extracts text from PDF reports, uses AI to identify key controls, maps them to frameworks, and delivers insights via email.

### What problem does this tool solve?
Reviewing SOC 2 reports manually is time-consuming and prone to inconsistency. This tool automates the process, ensuring consistent analysis and saving significant time for GRC professionals.

### Do I need technical expertise to use this tool?
No, the tool is designed to be user-friendly for GRC professionals without technical expertise. The deployment process is documented step-by-step, and once deployed, using the tool is as simple as uploading a PDF to an S3 bucket.

## Deployment Questions

### How long does deployment take?
The deployment process typically takes 15-20 minutes, including the time to upload the Lambda code package and deploy the CloudFormation stack.

### Can I deploy this in any AWS region?
Yes, you can deploy this solution in any AWS region that supports the required services (S3, Lambda, Textract, Bedrock, and SES). However, note that some services like Bedrock may not be available in all regions.

### Do I need to create any resources before deployment?
You only need to create an S3 bucket to store the Lambda code package before deployment. The CloudFormation template will create all other required resources.

### What happens if deployment fails?
If deployment fails, the CloudFormation stack will automatically roll back, removing any resources that were created. You can check the CloudFormation events to identify the cause of the failure.

## Usage Questions

### How do I use the tool after deployment?
Simply upload a SOC 2 report PDF to the S3 bucket created during deployment (in the "reports/" folder). The analysis will start automatically, and results will be sent to your email.

### How long does it take to analyze a report?
Analysis time depends on the size of the report. Typically, a 75-page report takes 5-10 minutes to analyze.

### What format are the analysis results delivered in?
Results are delivered as an HTML email containing an executive summary, quality rating, key controls identified, framework mappings, and identified gaps.

### Can I analyze multiple reports at once?
Yes, you can upload multiple reports to the S3 bucket. Each report will be processed independently, and you'll receive separate email notifications for each.

## Technical Questions

### What AWS services does this tool use?
The tool uses Amazon S3 for storage, AWS Lambda for processing, Amazon Textract for text extraction, Amazon Bedrock for AI analysis, and Amazon SES for sending emails.

### How much does it cost to run this tool?
The estimated cost per report analysis (75-page report) is approximately $0.33, including Textract (~$0.11), Bedrock (~$0.21), Lambda (~$0.005), and negligible costs for SES and S3.

### Is my data secure?
Yes, all data is encrypted at rest using SSE-S3, all data transfers use HTTPS (TLS), and IAM roles follow the principle of least privilege. No sensitive data is included in object tags.

### Can I customize the analysis parameters?
The basic deployment uses default parameters that work well for most SOC 2 reports. For advanced customization, you would need to modify the Lambda code, which may require technical expertise.

## Troubleshooting Questions

### I didn't receive an email with the analysis results. What should I do?
Check your spam/junk folder, verify that your email address is correct and verified in Amazon SES, and ensure that the report was uploaded to the correct S3 path. You can also check CloudWatch logs for any errors.

### How do I check if my report is being processed?
You can check the CloudWatch logs for the Lambda function to see if it's processing your report. You can also check if the report has been tagged with an analysis date in the S3 console.

### Can I reanalyze a report?
Yes, you can reanalyze a report by uploading it again to the S3 bucket. The tool will process it as a new report.

### Who do I contact for support?
For support, contact your IT team or the person who deployed the tool. If you deployed it yourself, refer to the troubleshooting section in the documentation. 