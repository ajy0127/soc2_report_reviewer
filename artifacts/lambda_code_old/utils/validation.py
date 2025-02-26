"""
Validation utilities for the SOC 2 Report Analysis Tool.
"""

import logging
import json
from utils.error_handling import ValidationError

logger = logging.getLogger()

def is_valid_pdf(file_key):
    """
    Check if the file has a PDF extension.
    
    Args:
        file_key (str): S3 object key
        
    Returns:
        bool: True if the file has a PDF extension, False otherwise
    """
    return file_key.lower().endswith('.pdf')

def validate_s3_event(event):
    """
    Validate the S3 event structure and extract bucket and key.
    
    Args:
        event (dict): S3 event
        
    Returns:
        tuple: (bucket_name, object_key)
        
    Raises:
        ValidationError: If the event is invalid
    """
    try:
        # Check if the event has records
        if not event.get('Records') or len(event['Records']) == 0:
            raise ValidationError("Invalid S3 event: No records found")
        
        # Get the first record
        record = event['Records'][0]
        
        # Check if it's an S3 event
        if record.get('eventSource') != 'aws:s3':
            raise ValidationError("Invalid event source: Not an S3 event")
        
        # Check if it's an ObjectCreated event
        if not record.get('eventName', '').startswith('ObjectCreated:'):
            raise ValidationError("Invalid event name: Not an ObjectCreated event")
        
        # Check if the record has s3 data
        if 's3' not in record:
            raise ValidationError("Invalid S3 event: No S3 data found")
        
        # Extract bucket and key
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']
        
        # Validate the key is a PDF
        if not is_valid_pdf(object_key):
            raise ValidationError(f"Invalid file type: {object_key} is not a PDF")
        
        return bucket_name, object_key
    
    except KeyError as e:
        raise ValidationError(f"Invalid S3 event structure: {str(e)}")

def validate_pdf_file(s3_client, bucket, key):
    """
    Validate that the file is a PDF and not too large.
    
    Args:
        s3_client: Boto3 S3 client
        bucket (str): S3 bucket name
        key (str): S3 object key
        
    Raises:
        ValidationError: If the file is not a PDF or too large
    """
    try:
        # Get object metadata
        response = s3_client.head_object(Bucket=bucket, Key=key)
        
        # Check content type
        content_type = response.get('ContentType', '')
        if 'application/pdf' not in content_type.lower():
            raise ValidationError(f"Invalid content type: {content_type}. Expected application/pdf")
        
        # Check file size (limit to 50MB)
        content_length = response.get('ContentLength', 0)
        max_size = 50 * 1024 * 1024  # 50MB
        if content_length > max_size:
            raise ValidationError(f"File too large: {content_length} bytes. Maximum allowed is {max_size} bytes")
        
    except Exception as e:
        if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == 'NoSuchKey':
            raise ValidationError(f"File not found: {key}")
        raise ValidationError(f"Error validating PDF file: {str(e)}")

def validate_analysis_result(result):
    """
    Validate the structure of the analysis result.
    
    Args:
        result (dict): Analysis result to validate
        
    Returns:
        bool: True if the result is valid
        
    Raises:
        ValidationError: If the result is invalid
    """
    required_keys = [
        'executive_summary', 'quality_rating', 'controls', 
        'framework_mappings', 'identified_gaps'
    ]
    
    # Check for required keys
    for key in required_keys:
        if key not in result:
            raise ValidationError(f"Missing required key: {key}")
    
    # Validate quality_rating is in range [0, 5]
    if not isinstance(result['quality_rating'], (int, float)):
        raise ValidationError("quality_rating must be a number")
    
    if not (0 <= result['quality_rating'] <= 5):
        raise ValidationError("quality_rating must be between 0 and 5")
    
    # Validate controls structure
    if not isinstance(result['controls'], list):
        raise ValidationError("controls must be a list")
    
    # Validate framework_mappings is a dictionary
    if not isinstance(result['framework_mappings'], dict):
        raise ValidationError("framework_mappings must be a dictionary")
    
    # Validate identified_gaps is a list
    if not isinstance(result['identified_gaps'], list):
        raise ValidationError("identified_gaps must be a list")
    
    return True

def validate_json_format(json_str):
    """
    Validate that a string is valid JSON.
    
    Args:
        json_str (str): JSON string to validate
        
    Returns:
        bool: True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError:
        return False 