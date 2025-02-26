# SOC 2 Report Analysis Tool - Implementation Plan

## 1. Project Setup and Infrastructure (Week 1)

### 1.1 Environment Setup
- [ ] Set up AWS account with appropriate permissions
- [ ] Install and configure AWS CLI
- [ ] Install and configure AWS CDK
- [ ] Set up version control repository

### 1.2 Infrastructure as Code
- [ ] Create CDK project structure
- [ ] Define S3 bucket with appropriate configuration:
  - Versioning enabled
  - SSE-S3 encryption
  - Event notifications for PDF uploads
- [ ] Define IAM roles with least privilege access
- [ ] Define Lambda function with appropriate timeout and memory
- [ ] Configure CloudWatch logging and metrics

## 2. Core Lambda Function Development (Week 2)

### 2.1 Lambda Handler Structure
- [ ] Create basic Lambda handler function
- [ ] Implement S3 event parsing
- [ ] Implement PDF extension validation
- [ ] Set up error handling and logging framework

### 2.2 Text Extraction with Textract
- [ ] Implement S3 object retrieval
- [ ] Implement Textract API integration
- [ ] Develop text consolidation from multiple pages
- [ ] Add error handling for Textract failures
- [ ] Implement retry logic for transient errors

### 2.3 AI Analysis with Bedrock
- [ ] Design prompt template for SOC 2 analysis
- [ ] Implement Bedrock API integration
- [ ] Develop JSON response parsing
- [ ] Add validation for response structure
- [ ] Implement error handling for Bedrock failures

## 3. Output and Notification Development (Week 3)

### 3.1 JSON Storage
- [ ] Implement JSON file creation
- [ ] Develop S3 upload functionality
- [ ] Add error handling for S3 operations

### 3.2 Email Notification
- [ ] Design HTML email template
- [ ] Implement SES integration
- [ ] Develop dynamic content generation
- [ ] Add error handling for SES operations

### 3.3 PDF Tagging
- [ ] Implement S3 object tagging
- [ ] Add timestamp generation in ISO-8601 format
- [ ] Add error handling for tagging operations

## 4. Testing and Validation (Week 4)

### 4.1 Unit Testing
- [ ] Develop unit tests for PDF validation
- [ ] Create mock responses for Textract
- [ ] Create mock responses for Bedrock
- [ ] Test S3 operations with mocks
- [ ] Test SES operations with mocks

### 4.2 Integration Testing
- [ ] Test end-to-end flow with sample PDFs
- [ ] Validate JSON output structure
- [ ] Verify email delivery
- [ ] Confirm PDF tagging

### 4.3 Performance Testing
- [ ] Test with large PDFs (75+ pages)
- [ ] Measure processing time
- [ ] Optimize Lambda memory/timeout if needed
- [ ] Test concurrent uploads

### 4.4 Security Testing
- [ ] Verify encryption at rest
- [ ] Verify TLS for all API calls
- [ ] Validate IAM permissions
- [ ] Check for sensitive data exposure

## 5. Deployment and Documentation (Week 5)

### 5.1 Deployment
- [ ] Create deployment pipeline
- [ ] Deploy to development environment
- [ ] Validate deployment
- [ ] Deploy to production environment

### 5.2 Monitoring Setup
- [ ] Configure CloudWatch dashboards
- [ ] Set up alarms for errors and performance
- [ ] Implement notification for alarms

### 5.3 Documentation
- [ ] Create technical documentation
- [ ] Document API specifications
- [ ] Create user guide
- [ ] Document troubleshooting procedures

## 6. Code Structure and Organization

### 6.1 Lambda Function Structure
```
lambda_code/
├── app.py                 # Main Lambda handler
├── textract_service.py    # Textract integration
├── bedrock_service.py     # Bedrock integration
├── s3_service.py          # S3 operations
├── ses_service.py         # Email operations
├── utils/
│   ├── validation.py      # Input validation
│   ├── logging.py         # Logging utilities
│   └── error_handling.py  # Error handling utilities
└── templates/
    └── email_template.html # Email template
```

### 6.2 CDK Structure
```
cdk/
├── app.py                 # CDK app entry point
├── soc2_analysis_stack.py # Main infrastructure stack
└── constructs/
    ├── s3_construct.py    # S3 bucket configuration
    ├── lambda_construct.py # Lambda configuration
    └── iam_construct.py   # IAM roles and policies
```

## 7. Detailed Implementation Notes

### 7.1 Lambda Handler (app.py)
```python
import json
import os
import logging
from datetime import datetime
import boto3
from textract_service import extract_text
from bedrock_service import analyze_text
from s3_service import store_analysis, tag_pdf
from ses_service import send_email
from utils.validation import is_valid_pdf
from utils.logging import setup_logging

logger = setup_logging()

def lambda_handler(event, context):
    """
    Main Lambda handler function that processes S3 events.
    """
    try:
        # Extract bucket and key from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Processing file: {key} from bucket: {bucket}")
        
        # Validate PDF extension
        if not is_valid_pdf(key):
            logger.warning(f"Skipping non-PDF file: {key}")
            return {
                'statusCode': 200,
                'body': json.dumps('Skipped non-PDF file')
            }
        
        # Extract text using Textract
        logger.info("Extracting text with Textract")
        extracted_text = extract_text(bucket, key)
        
        # Analyze text using Bedrock
        logger.info("Analyzing text with Bedrock")
        analysis_result = analyze_text(extracted_text)
        
        # Store analysis as JSON
        logger.info("Storing analysis results")
        analysis_key = key.replace('.pdf', ' - AI Analysis.json')
        store_analysis(bucket, analysis_key, analysis_result)
        
        # Send email notification
        logger.info("Sending email notification")
        stakeholder_email = os.environ.get('STAKEHOLDER_EMAIL', 'default@example.com')
        report_name = os.path.basename(key)
        send_email(stakeholder_email, report_name, analysis_result)
        
        # Tag the original PDF
        logger.info("Tagging original PDF")
        timestamp = datetime.utcnow().isoformat()
        tag_pdf(bucket, key, 'report-run-date', timestamp)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
```

### 7.2 Textract Service (textract_service.py)
```python
import boto3
import logging

logger = logging.getLogger()

def extract_text(bucket, key):
    """
    Extract text from a PDF using Amazon Textract.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        str: Extracted text
    """
    textract = boto3.client('textract')
    
    try:
        # For smaller documents, use synchronous API
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text from response
        text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text'] + "\n"
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}", exc_info=True)
        raise
```

### 7.3 Bedrock Service (bedrock_service.py)
```python
import boto3
import json
import logging

logger = logging.getLogger()

def analyze_text(text):
    """
    Analyze text using Amazon Bedrock.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        dict: Analysis result
    """
    bedrock_client = boto3.client('bedrock-runtime')
    
    try:
        prompt = f"""
        You are a cybersecurity expert analyzing a SOC 2 report.
        Extract the scope, list key controls, map them to CIS Top 20 and OWASP Top 10,
        identify gaps, provide a summary, and a 0-10 quality rating.
        Return valid JSON with keys:
        "scope", "controls", "cis_mapping", "owasp_mapping", "gaps", "summary", "quality_rating".

        The report text is:
        {text}
        """
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'prompt': prompt,
                'max_tokens_to_sample': 4000,
                'temperature': 0.2
            })
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        result_text = response_body['completion']
        
        # Extract JSON from the response
        # This assumes the model returns valid JSON
        # In practice, you might need more robust parsing
        result_json = json.loads(result_text)
        
        # Validate the result structure
        validate_result(result_json)
        
        return result_json
        
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}", exc_info=True)
        raise

def validate_result(result):
    """
    Validate the structure of the analysis result.
    
    Args:
        result (dict): Analysis result to validate
        
    Raises:
        ValueError: If the result is invalid
    """
    required_keys = [
        'scope', 'controls', 'cis_mapping', 
        'owasp_mapping', 'gaps', 'summary', 
        'quality_rating'
    ]
    
    for key in required_keys:
        if key not in result:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate quality_rating is in range [0, 10]
    if not (0 <= result['quality_rating'] <= 10):
        raise ValueError("quality_rating must be between 0 and 10")
```

### 7.4 S3 Service (s3_service.py)
```python
import boto3
import json
import logging

logger = logging.getLogger()

def store_analysis(bucket, key, analysis):
    """
    Store analysis result as JSON in S3.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        analysis (dict): Analysis result
    """
    s3 = boto3.client('s3')
    
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(analysis, indent=2),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"Analysis stored at s3://{bucket}/{key}")
        
    except Exception as e:
        logger.error(f"Error storing analysis: {str(e)}", exc_info=True)
        raise

def tag_pdf(bucket, key, tag_key, tag_value):
    """
    Tag a PDF object in S3.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        tag_key (str): Tag key
        tag_value (str): Tag value
    """
    s3 = boto3.client('s3')
    
    try:
        s3.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={
                'TagSet': [
                    {
                        'Key': tag_key,
                        'Value': tag_value
                    }
                ]
            }
        )
        
        logger.info(f"Tagged object s3://{bucket}/{key} with {tag_key}={tag_value}")
        
    except Exception as e:
        logger.error(f"Error tagging PDF: {str(e)}", exc_info=True)
        raise
```

### 7.5 SES Service (ses_service.py)
```python
import boto3
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger()

def send_email(recipient, report_name, analysis):
    """
    Send email notification with analysis results.
    
    Args:
        recipient (str): Email recipient
        report_name (str): Name of the report
        analysis (dict): Analysis result
    """
    ses = boto3.client('ses')
    sender = "soc2-analysis@example.com"  # Must be verified in SES
    
    try:
        # Create HTML content
        html_content = create_html_content(report_name, analysis)
        
        # Create email message
        message = MIMEMultipart()
        message['Subject'] = f"SOC 2 Report Analysis: {report_name}"
        message['From'] = sender
        message['To'] = recipient
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send email
        response = ses.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={
                'Data': message.as_string()
            }
        )
        
        logger.info(f"Email sent to {recipient}, message ID: {response['MessageId']}")
        
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}", exc_info=True)
        raise

def create_html_content(report_name, analysis):
    """
    Create HTML content for email.
    
    Args:
        report_name (str): Name of the report
        analysis (dict): Analysis result
        
    Returns:
        str: HTML content
    """
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333366; }}
            h2 {{ color: #333366; margin-top: 20px; }}
            .section {{ margin-bottom: 20px; }}
            .rating {{ font-size: 24px; font-weight: bold; }}
            .control {{ margin-bottom: 10px; }}
            .compliant {{ color: green; }}
            .non-compliant {{ color: red; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SOC 2 Report Analysis: {report_name}</h1>
            
            <div class="section">
                <h2>Summary</h2>
                <p>{analysis['summary']}</p>
            </div>
            
            <div class="section">
                <h2>Quality Rating</h2>
                <p class="rating">{analysis['quality_rating']}/10</p>
            </div>
            
            <div class="section">
                <h2>Scope</h2>
                <p>{analysis['scope']}</p>
            </div>
            
            <div class="section">
                <h2>Controls</h2>
                <ul>
    """
    
    for control in analysis['controls']:
        status_class = "compliant" if control['status'] == "Compliant" else "non-compliant"
        html += f'<li class="control"><span class="{status_class}">{control["name"]}</span> - {control["status"]}</li>'
    
    html += """
                </ul>
            </div>
            
            <div class="section">
                <h2>CIS Mapping</h2>
                <h3>Mapped Controls</h3>
                <ul>
    """
    
    for control in analysis['cis_mapping']['mapped']:
        html += f'<li>{control}</li>'
    
    html += """
                </ul>
                <h3>Gaps</h3>
                <ul>
    """
    
    for gap in analysis['cis_mapping']['gaps']:
        html += f'<li>{gap}</li>'
    
    html += """
                </ul>
            </div>
            
            <div class="section">
                <h2>OWASP Mapping</h2>
                <h3>Mapped Controls</h3>
                <ul>
    """
    
    for control in analysis['owasp_mapping']['mapped']:
        html += f'<li>{control}</li>'
    
    html += """
                </ul>
                <h3>Gaps</h3>
                <ul>
    """
    
    for gap in analysis['owasp_mapping']['gaps']:
        html += f'<li>{gap}</li>'
    
    html += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Identified Gaps</h2>
                <ul>
    """
    
    for gap in analysis['gaps']:
        html += f'<li>{gap}</li>'
    
    html += """
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
```

## 8. AWS CDK Implementation

### 8.1 Main Stack (soc2_analysis_stack.py)
```python
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as _lambda,
    aws_iam as iam,
    core
)

class Soc2AnalysisStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket for reports
        reports_bucket = s3.Bucket(
            self,
            "Soc2ReportsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED
        )

        # Lambda function
        lambda_fn = _lambda.Function(
            self,
            "Soc2AnalysisLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("lambda_code"),
            timeout=core.Duration.minutes(10),
            memory_size=1024,
            environment={
                "STAKEHOLDER_EMAIL": "compliance@example.com"
            }
        )

        # Permissions
        reports_bucket.grant_read(lambda_fn)
        reports_bucket.grant_write(lambda_fn)
        
        # For tagging objects
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObjectTagging"],
                resources=[reports_bucket.arn_for_objects("*")]
            )
        )

        # Textract permissions
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "textract:DetectDocumentText",
                    "textract:AnalyzeDocument"
                ],
                resources=["*"]
            )
        )

        # Bedrock permissions
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )

        # SES permissions
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail"
                ],
                resources=["*"]
            )
        )

        # Notification for PDF upload
        notification = s3n.LambdaDestination(lambda_fn)
        reports_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            notification,
            s3.NotificationKeyFilter(prefix="reports/", suffix=".pdf")
        )
```

### 8.2 CDK App (app.py)
```python
#!/usr/bin/env python3

from aws_cdk import core
from soc2_analysis_stack import Soc2AnalysisStack

app = core.App()
Soc2AnalysisStack(app, "Soc2AnalysisStack")

app.synth()
```

## 9. Testing Strategy

### 9.1 Unit Tests
- Test PDF validation function
- Test Textract text extraction with mock responses
- Test Bedrock analysis with mock responses
- Test S3 operations with mock S3 client
- Test SES email generation and sending with mock SES client

### 9.2 Integration Tests
- Test end-to-end flow with sample PDFs
- Verify JSON output structure matches expected format
- Verify email delivery and content
- Confirm PDF tagging with correct timestamp

### 9.3 Performance Tests
- Test with large PDFs (75+ pages)
- Measure processing time and optimize if needed
- Test concurrent uploads to ensure scalability

## 10. Deployment Checklist

- [ ] Verify AWS account has necessary service limits
- [ ] Ensure SES sender email is verified
- [ ] Deploy infrastructure with CDK
- [ ] Verify S3 bucket configuration
- [ ] Verify Lambda function configuration
- [ ] Test with sample PDF upload
- [ ] Monitor CloudWatch logs for errors
- [ ] Set up CloudWatch alarms
- [ ] Document deployment process 