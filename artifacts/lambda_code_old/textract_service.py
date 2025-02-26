"""
Textract service for the SOC 2 Report Analysis Tool.
"""

import boto3
import logging
import time
from botocore.exceptions import ClientError
from utils.error_handling import TextractError, retry

logger = logging.getLogger()

@retry(max_attempts=3, delay=2, backoff=2, exceptions=(ClientError,))
def extract_text(bucket, key):
    """
    Extract text from a PDF using Amazon Textract.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        str: Extracted text
        
    Raises:
        TextractError: If text extraction fails
    """
    textract = boto3.client('textract')
    
    try:
        logger.info(f"Starting text extraction for s3://{bucket}/{key}")
        
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
        
        logger.info(f"Extracted {len(text)} characters of text")
        
        # If no text was extracted, try to use AnalyzeDocument instead
        # This is useful for scanned PDFs
        if not text.strip():
            logger.info("No text extracted with DetectDocumentText, trying AnalyzeDocument")
            text = extract_text_with_analyze_document(bucket, key)
        
        return text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'InvalidS3ObjectException':
            raise TextractError(f"The S3 object does not exist or is not accessible: {error_message}")
        elif error_code == 'InvalidDocumentException':
            raise TextractError(f"The document is invalid or corrupted: {error_message}")
        elif error_code == 'UnsupportedDocumentException':
            raise TextractError(f"The document format is not supported: {error_message}")
        elif error_code == 'DocumentTooLargeException':
            logger.info("Document is too large for synchronous processing, using asynchronous API")
            return extract_text_async(bucket, key)
        elif error_code == 'ProvisionedThroughputExceededException':
            raise TextractError(f"Provisioned throughput exceeded: {error_message}")
        elif error_code == 'ThrottlingException':
            raise TextractError(f"Throttling exception: {error_message}")
        elif error_code == 'AccessDeniedException':
            raise TextractError(f"Access denied: {error_message}")
        else:
            raise TextractError(f"Textract error: {error_code} - {error_message}")
    except Exception as e:
        raise TextractError(f"Error extracting text: {str(e)}")

@retry(max_attempts=3, delay=2, backoff=2, exceptions=(ClientError,))
def extract_text_with_analyze_document(bucket, key):
    """
    Extract text from a PDF using Amazon Textract AnalyzeDocument.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        str: Extracted text
        
    Raises:
        TextractError: If text extraction fails
    """
    textract = boto3.client('textract')
    
    try:
        logger.info(f"Starting text extraction with AnalyzeDocument for s3://{bucket}/{key}")
        
        response = textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            FeatureTypes=['TABLES', 'FORMS']
        )
        
        # Extract text from response
        text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text'] + "\n"
        
        logger.info(f"Extracted {len(text)} characters of text with AnalyzeDocument")
        
        return text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'DocumentTooLargeException':
            logger.info("Document is too large for synchronous processing, using asynchronous API")
            return extract_text_async(bucket, key)
        else:
            raise TextractError(f"Textract AnalyzeDocument error: {error_code} - {error_message}")
    except Exception as e:
        raise TextractError(f"Error extracting text with AnalyzeDocument: {str(e)}")

def extract_text_async(bucket, key):
    """
    Extract text from a large PDF using asynchronous Textract operations.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Returns:
        str: Extracted text
        
    Raises:
        TextractError: If text extraction fails
    """
    textract = boto3.client('textract')
    
    try:
        logger.info(f"Starting asynchronous text extraction for s3://{bucket}/{key}")
        
        # Start asynchronous job
        response = textract.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        job_id = response['JobId']
        logger.info(f"Started asynchronous job with ID: {job_id}")
        
        # Wait for job to complete
        status = 'IN_PROGRESS'
        while status == 'IN_PROGRESS':
            time.sleep(5)
            response = textract.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            logger.info(f"Job status: {status}")
        
        # Check if job failed
        if status == 'FAILED':
            raise TextractError(f"Asynchronous job failed: {response.get('StatusMessage', 'Unknown error')}")
        
        # Get results
        pages = []
        
        # Get first page of results
        pages.append(response)
        
        # Check if there are more pages of results
        next_token = response.get('NextToken')
        while next_token:
            response = textract.get_document_text_detection(
                JobId=job_id,
                NextToken=next_token
            )
            pages.append(response)
            next_token = response.get('NextToken')
        
        # Extract text from all pages
        text = ""
        for page in pages:
            for item in page['Blocks']:
                if item['BlockType'] == 'LINE':
                    text += item['Text'] + "\n"
        
        logger.info(f"Extracted {len(text)} characters of text asynchronously")
        
        return text
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise TextractError(f"Textract asynchronous error: {error_code} - {error_message}")
    except Exception as e:
        raise TextractError(f"Error extracting text asynchronously: {str(e)}") 