#!/usr/bin/env python3
"""
Local test script for the SOC2 Report Reviewer Lambda function.
"""

import json
import os
import sys
import boto3
import logging
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Add the lambda_package directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Lambda handler
from app import lambda_handler

def load_event(event_file):
    """Load an event from a JSON file."""
    with open(event_file, 'r') as f:
        return json.load(f)

def mock_aws_services():
    """Mock AWS services for local testing."""
    # Mock S3 client
    s3_mock = MagicMock()
    s3_mock.get_object.return_value = {
        'Body': MagicMock(),
        'ContentLength': 1024,
        'ContentType': 'application/pdf'
    }
    s3_mock.head_object.return_value = {
        'ContentLength': 1024,
        'ContentType': 'application/pdf'
    }
    s3_mock.put_object.return_value = {}
    
    # Mock Textract client
    textract_mock = MagicMock()
    textract_mock.detect_document_text.return_value = {
        'Blocks': [
            {
                'BlockType': 'LINE',
                'Text': 'This is a sample SOC2 report.'
            },
            {
                'BlockType': 'LINE',
                'Text': 'Control Environment: The organization maintains a strong control environment.'
            },
            {
                'BlockType': 'LINE',
                'Text': 'Risk Assessment: The organization has a comprehensive risk assessment process.'
            }
        ]
    }
    
    # Mock Bedrock client
    bedrock_mock = MagicMock()
    bedrock_mock.invoke_model.return_value = {
        'body': MagicMock(),
    }
    bedrock_mock.invoke_model.return_value['body'].read.return_value = json.dumps({
        'content': json.dumps({
            'executive_summary': 'This is a high-quality SOC2 report with comprehensive controls.',
            'quality_rating': 4,
            'controls': [
                {
                    'id': 'C1',
                    'name': 'Access Control',
                    'description': 'The organization implements strong access controls.',
                    'effectiveness': 'Effective'
                },
                {
                    'id': 'C2',
                    'name': 'Change Management',
                    'description': 'The organization has a robust change management process.',
                    'effectiveness': 'Effective'
                }
            ],
            'framework_mappings': {
                'CIS': ['1.1', '1.2'],
                'OWASP': ['A1', 'A2']
            },
            'identified_gaps': []
        })
    }).encode()
    
    # Mock SES client
    ses_mock = MagicMock()
    ses_mock.send_email.return_value = {
        'MessageId': '12345'
    }
    
    # Mock STS client
    sts_mock = MagicMock()
    sts_mock.get_caller_identity.return_value = {
        'Arn': 'arn:aws:iam::123456789012:role/lambda-role'
    }
    
    # Create a mock for boto3.client
    def mock_boto3_client(service_name, **kwargs):
        if service_name == 's3':
            return s3_mock
        elif service_name == 'textract':
            return textract_mock
        elif service_name == 'bedrock-runtime':
            return bedrock_mock
        elif service_name == 'ses':
            return ses_mock
        elif service_name == 'sts':
            return sts_mock
        else:
            return MagicMock()
    
    # Create patch objects
    patches = [
        patch('boto3.client', side_effect=mock_boto3_client)
    ]
    
    return patches

def main():
    """Run the local test."""
    # Load the event
    event = load_event('../events/s3-event.json')
    
    # Set environment variables
    os.environ['ENVIRONMENT'] = 'dev'
    os.environ['REPORTS_BUCKET'] = 'soc2-reports-local'
    os.environ['STAKEHOLDER_EMAIL'] = 'test@example.com'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    os.environ['YOLO_MODE'] = 'true'
    
    # Apply mocks
    patches = mock_aws_services()
    for p in patches:
        p.start()
    
    try:
        # Invoke the Lambda handler
        logger.info("Invoking Lambda handler with event: %s", json.dumps(event, indent=2))
        response = lambda_handler(event, {})
        logger.info("Lambda handler response: %s", json.dumps(response, indent=2))
    finally:
        # Stop mocks
        for p in patches:
            p.stop()

if __name__ == "__main__":
    main() 