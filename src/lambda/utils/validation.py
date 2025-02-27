import json
import logging
from typing import Tuple

logger = logging.getLogger()

class ValidationError(Exception):
    """
    Custom exception class for validation errors.
    
    This exception is raised when validation of events or files fails.
    It allows for specific error handling for validation issues.
    """
    pass

def validate_event(event) -> Tuple[str, str]:
    """
    Validates the incoming S3 event and extracts bucket name and object key.
    
    This function handles multiple event formats:
    1. Direct invocation with custom event format
    2. EventBridge events from S3
    3. S3 notification events
    
    Args:
        event (dict): The Lambda event object
        
    Returns:
        Tuple[str, str]: A tuple containing (bucket_name, object_key)
        
    Raises:
        ValidationError: If the event is invalid or missing required fields
    """
    logger.info("Validating event")
    
    # Check if event is None or empty
    if not event:
        # Reject empty events immediately
        raise ValidationError("Event is empty or None")
    
    try:
        # Case 1: Direct invocation with custom event
        # Format: {'bucket': 'bucket-name', 'key': 'object-key'}
        if 'bucket' in event and 'key' in event:
            bucket_name = event['bucket']
            object_key = event['key']
            return bucket_name, object_key
        
        # Case 2: S3 event via EventBridge
        # Format: {'detail': {'bucket': {'name': 'bucket-name'}, 'object': {'key': 'object-key'}}}
        if 'detail' in event:
            detail = event['detail']
            bucket_name = detail['bucket']['name']
            object_key = detail['object']['key']
            return bucket_name, object_key
            
        # Case 3: S3 event via direct notification
        # Format: {'Records': [{'eventSource': 'aws:s3', 's3': {'bucket': {'name': 'bucket-name'}, 'object': {'key': 'object-key'}}}]}
        if 'Records' in event:
            record = event['Records'][0]
            if record['eventSource'] == 'aws:s3':
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']
                return bucket_name, object_key
        
        # If we reach here, the event format is not recognized
        raise ValidationError("Event structure not recognized")
    
    except (KeyError, IndexError) as e:
        # This catches missing keys or indices in the event structure
        logger.error(f"Error parsing event: {str(e)}")
        raise ValidationError(f"Invalid event structure: {str(e)}")

def validate_pdf_file(file_content: bytes) -> bool:
    """
    Validates that the file is a valid PDF.
    
    This function performs basic validation of PDF files by checking:
    1. The file starts with the PDF signature (%PDF-)
    2. Optionally, the file ends with the EOF marker (%%EOF)
    
    Args:
        file_content (bytes): The file content to validate
        
    Returns:
        bool: True if the file is a valid PDF, False otherwise
        
    Raises:
        ValidationError: If the file is not a valid PDF
    """
    # Check PDF signature
    # All valid PDFs start with %PDF-
    if not file_content.startswith(b'%PDF-'):
        raise ValidationError("Invalid file format: Not a PDF file")
    
    # Check for EOF marker (optional but good practice)
    # Valid PDFs typically end with %%EOF
    if not file_content.rstrip().endswith(b'%%EOF'):
        # This is just a warning, not an error
        logger.warning("PDF file may be incomplete or corrupted (no EOF marker)")
    
    return True 