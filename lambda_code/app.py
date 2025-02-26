"""
Main Lambda handler for the SOC 2 Report Analysis Tool.
"""

import json
import os
import logging
from datetime import datetime, UTC
import boto3
import traceback

# Import services
from textract_service import extract_text
from bedrock_service import analyze_text
from s3_service import store_analysis, tag_pdf
from ses_service import send_email

# Import utilities
from utils.validation import validate_s3_event, validate_pdf_file
from utils.error_handling import ValidationError, TextractError, BedrockError, S3Error, SESError, handle_exceptions
from utils.logging import setup_logging, log_event, log_error

# Set up logging
logger = setup_logging()

@handle_exceptions
def lambda_handler(event, context):
    """
    Main Lambda handler function that processes S3 events.
    
    Args:
        event (dict): Lambda event
        context (LambdaContext): Lambda context
        
    Returns:
        dict: Response object
    """
    # Log the event (with sensitive information redacted)
    log_event(logger, event)
    
    try:
        # Extract bucket and key from event
        bucket, key = validate_s3_event(event)
        
        logger.info(f"Processing file: {key} from bucket: {bucket}")
        
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Validate PDF file
        validate_pdf_file(s3_client, bucket, key)
        
        # Extract text using Textract
        logger.info("Extracting text with Textract")
        extracted_text = extract_text(bucket, key)
        
        # Log the length of extracted text
        logger.info(f"Extracted {len(extracted_text)} characters of text")
        
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
        timestamp = datetime.now(UTC).isoformat()
        tag_pdf(bucket, key, 'report-run-date', timestamp)
        
        logger.info("Processing completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed SOC 2 report',
                'report': key,
                'analysis': analysis_key,
                'timestamp': timestamp
            })
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': f"Invalid S3 event or PDF file: {str(e)}"
            })
        }
    except (TextractError, BedrockError, S3Error, SESError) as e:
        logger.error(f"Processing error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
    except Exception as e:
        # Log the error with stack trace
        log_error(logger, "Unexpected error processing file", e)
        
        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Unexpected error: {str(e)}",
                'trace': traceback.format_exc()
            })
        }

def process_large_pdf(bucket, key):
    """
    Process a large PDF using asynchronous Textract operations.
    This is a placeholder for future implementation.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        str: Extracted text
    """
    # This would implement the asynchronous Textract workflow
    # for PDFs that are too large for synchronous processing
    logger.info("Using asynchronous Textract processing for large PDF")
    
    # Placeholder - would implement StartDocumentTextDetection and
    # GetDocumentTextDetection with polling
    
    raise NotImplementedError("Asynchronous processing not yet implemented") 