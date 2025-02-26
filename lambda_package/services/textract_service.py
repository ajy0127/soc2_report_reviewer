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
        
        # Check if the S3 object exists and is accessible
        try:
            s3_client = boto3.client('s3')
            logger.info(f"Checking S3 object accessibility in Textract: s3://{bucket}/{key}")
            
            # In YOLO mode, instead of validating, let's try to download the file first
            # This might help bypass some permission issues
            try:
                response = s3_client.get_object(Bucket=bucket, Key=key)
                logger.info(f"Successfully accessed the object: {key}, size: {response.get('ContentLength', 0)}")
            except Exception as s3_error:
                logger.error(f"Error accessing the S3 object directly: {str(s3_error)}")
                if '403' in str(s3_error):
                    logger.error(f"Access denied (403) when trying to get object directly. Proceeding with Textract anyway.")
                # We'll continue with Textract even if this fails
        except Exception as e:
            logger.warning(f"Error checking S3 object: {str(e)}")
            # Continue with Textract anyway
        
        # For smaller documents, use synchronous API
        try:
            logger.info(f"Calling Textract.detect_document_text for s3://{bucket}/{key}")
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
        except ClientError as client_error:
            logger.error(f"Textract detect_document_text ClientError: {str(client_error)}")
            error_code = client_error.response['Error']['Code']
            
            if error_code == 'InvalidS3ObjectException':
                # The S3 object doesn't exist or Textract can't access it
                # This could be due to the role not having textract:* permissions on the resource
                logger.error(f"InvalidS3ObjectException: Textract couldn't access the S3 object")
                raise TextractError(f"The S3 object does not exist or is not accessible: {client_error.response['Error']['Message']}")
            elif error_code == 'AccessDeniedException':
                logger.error(f"AccessDeniedException: Textract doesn't have permission to access the S3 object or Lambda doesn't have permission to call Textract")
                # Try analyze_document as a fallback
                logger.info("Trying AnalyzeDocument as fallback for AccessDeniedException")
                return extract_text_with_analyze_document(bucket, key)
            else:
                # For other errors, try the fallback or raise
                try:
                    logger.info(f"Trying AnalyzeDocument as fallback for error: {error_code}")
                    return extract_text_with_analyze_document(bucket, key)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    raise TextractError(f"Textract error: {error_code} - {client_error.response['Error']['Message']}")
        
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