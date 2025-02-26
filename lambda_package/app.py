"""
Main Lambda handler for the SOC2 Report Reviewer application.

This module serves as the entry point for the AWS Lambda function that processes
SOC2 reports uploaded to S3. It orchestrates the entire workflow:
1. Validates the incoming S3 event
2. Retrieves the PDF file from S3
3. Extracts text from the PDF using Amazon Textract
4. Analyzes the text using Amazon Bedrock (Claude model)
5. Stores the analysis results back to S3
6. Sends a notification email with the analysis summary

The Lambda function supports a "YOLO mode" for development and testing,
which allows processing to continue despite certain errors.
"""

import json
import os
import logging
import urllib.parse
import boto3
from botocore.exceptions import ClientError
import traceback

# Set up logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Import service modules - each handles a specific AWS service interaction
from services.s3_service import get_object, store_result
from services.textract_service import extract_text
from services.bedrock_service import analyze_text
from services.ses_service import send_notification

# Import utility modules - for validation and error handling
from utils.validation import validate_event, validate_file
from utils.error_handling import handle_error, ServiceError

def lambda_handler(event, context):
    """
    Main Lambda handler function that processes S3 events when a SOC2 report is uploaded.
    
    This function implements the complete workflow for processing SOC2 reports:
    1. Validates the S3 event and extracts bucket/key information
    2. Retrieves the PDF file from S3
    3. Extracts text using Amazon Textract
    4. Analyzes the text using Amazon Bedrock (Claude model)
    5. Stores the analysis results back to S3
    6. Sends a notification email with the analysis summary
    
    The function supports a "YOLO mode" that allows processing to continue
    despite certain errors, which is useful for development and testing.
    
    Args:
        event (dict): Lambda event containing S3 event information
        context (LambdaContext): Lambda context object with runtime information
        
    Returns:
        dict: Response object with status code and result information
    """
    # Enable YOLO mode if specified in environment variables or event
    # YOLO mode allows processing to continue despite certain errors
    yolo_mode = os.environ.get('YOLO_MODE', 'false').lower() == 'true'
    if 'yolo_mode' in event:
        yolo_mode = event['yolo_mode']
    
    if yolo_mode:
        logger.info("YOLO mode enabled - will continue processing despite certain errors")
    
    try:
        # Log the event for debugging purposes
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Step 1: Validate the event and extract bucket and key
        # This ensures we're processing a valid S3 event with a PDF file
        logger.info("Validating event")
        bucket_name, object_key = validate_event(event)
        logger.info(f"Extracted from S3 event: bucket={bucket_name}, key={object_key}")
        logger.info(f"Processing file: {object_key} from bucket: {bucket_name}")
        
        # URL decode the key if needed (S3 keys can be URL-encoded in events)
        decoded_key = urllib.parse.unquote_plus(object_key)
        if decoded_key != object_key:
            logger.info(f"Decoded key: {decoded_key}")
            object_key = decoded_key
        
        # Step 2: Validate the file exists and is a PDF
        logger.info(f"Validating file: bucket={bucket_name}, key={object_key}")
        validate_file(bucket_name, object_key)
        
        # Step 3: Get the file from S3
        try:
            s3_response = get_object(bucket_name, object_key)
            logger.info(f"Retrieved object from S3: {object_key}")
        except ServiceError as e:
            logger.error(f"Error retrieving object from S3: {str(e)}")
            if not yolo_mode:
                # In normal mode, propagate the error
                raise
            # In YOLO mode, continue with a mock response
            s3_response = {'Body': None}
            logger.warning("Using mock S3 response in YOLO mode")
        
        # Step 4: Extract text from the file using Amazon Textract
        try:
            if s3_response['Body']:
                logger.info(f"Starting text extraction for s3://{bucket_name}/{object_key}")
                extracted_text = extract_text(bucket_name, object_key)
                logger.info(f"Extracted text from file (length: {len(extracted_text)})")
            else:
                # In YOLO mode with no file body, use a placeholder
                extracted_text = "This is a placeholder for extracted text in YOLO mode."
                logger.warning("Using placeholder text in YOLO mode")
        except ServiceError as e:
            logger.error(f"Error extracting text: {str(e)}")
            if not yolo_mode:
                raise
            # In YOLO mode, continue with a placeholder
            extracted_text = "This is a placeholder for extracted text in YOLO mode."
            logger.warning("Using placeholder text in YOLO mode")
        
        # Step 5: Analyze the text using Amazon Bedrock (Claude model)
        try:
            logger.info("Starting AI analysis with model: anthropic.claude-3-sonnet-20240229-v1:0")
            analysis_result = analyze_text(extracted_text)
            logger.info("Successfully analyzed text")
        except ServiceError as e:
            logger.error(f"Error analyzing text: {str(e)}")
            if not yolo_mode:
                raise
            # In YOLO mode, continue with a mock result
            analysis_result = {
                "executive_summary": "This is a mock analysis result in YOLO mode.",
                "quality_rating": 3,
                "controls": [],
                "framework_mappings": {},
                "identified_gaps": []
            }
            logger.warning("Using mock analysis result in YOLO mode")
        
        # Step 6: Store the analysis result back to S3
        result_key = object_key.replace('.pdf', '_analysis.json')
        try:
            store_result(bucket_name, result_key, analysis_result)
            logger.info(f"Analysis stored at s3://{bucket_name}/{result_key}")
            logger.info(f"Stored analysis result at {result_key}")
        except ServiceError as e:
            logger.error(f"Error storing result: {str(e)}")
            if not yolo_mode:
                raise
            logger.warning("Skipping result storage in YOLO mode")
        
        # Step 7: Send notification email to stakeholders
        try:
            stakeholder_email = os.environ.get('STAKEHOLDER_EMAIL', 'default@example.com')
            send_notification(stakeholder_email, object_key, analysis_result)
            logger.info(f"Sent notification to {stakeholder_email}")
        except ServiceError as e:
            logger.error(f"Error sending notification: {str(e)}")
            if not yolo_mode:
                raise
            logger.warning("Skipping notification in YOLO mode")
        
        # Return success response with information about the processed files
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis completed successfully',
                'report': object_key,
                'analysis': result_key
            })
        }
        
    except ServiceError as e:
        # Handle service-specific errors (S3, Textract, Bedrock, SES)
        # The handle_error function formats the error response appropriately
        return handle_error(e)
    except Exception as e:
        # Handle unexpected errors with detailed logging for troubleshooting
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Unexpected error: {str(e)}",
                'trace': traceback.format_exc()
            })
        } 