"""
Validation utilities for the SOC2 Report Reviewer application.
"""

import logging
import json
import urllib.parse
import boto3
from botocore.exceptions import ClientError

from utils.error_handling import ValidationError

logger = logging.getLogger()

def validate_event(event):
    """
    Validate the event and extract bucket and key.
    
    Args:
        event (dict): The event to validate
        
    Returns:
        tuple: (bucket_name, object_key)
        
    Raises:
        ValidationError: If the event is invalid
    """
    logger.info("Validating event")
    
    try:
        # Check if this is an S3 event (has 'Records' field)
        if 'Records' in event and len(event['Records']) > 0:
            record = event['Records'][0]
            
            # Check if it's an S3 event
            if 's3' not in record:
                raise ValidationError("Invalid event: Not an S3 event")
            
            # Extract bucket and key
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']
            
            logger.info(f"Extracted from S3 event: bucket={bucket_name}, key={object_key}")
            return bucket_name, object_key
            
        # Check if this is an EventBridge event (has 'detail' field)
        elif 'detail' in event and isinstance(event['detail'], dict):
            detail = event['detail']
            
            # Check if detail has bucket and object
            if 'bucket' not in detail or 'object' not in detail:
                raise ValidationError("Invalid EventBridge event: Missing bucket or object")
            
            # Extract bucket and key
            if isinstance(detail['bucket'], dict) and 'name' in detail['bucket']:
                bucket_name = detail['bucket']['name']
            else:
                bucket_name = detail['bucket']
                
            if isinstance(detail['object'], dict) and 'key' in detail['object']:
                object_key = detail['object']['key']
            else:
                object_key = detail['object']
                
            logger.info(f"Extracted from EventBridge event: bucket={bucket_name}, key={object_key}")
            return bucket_name, object_key
            
        # Check if this is a direct invocation with bucket and key
        elif 'bucket' in event and 'key' in event:
            bucket_name = event['bucket']
            object_key = event['key']
            
            logger.info(f"Extracted from direct invocation: bucket={bucket_name}, key={object_key}")
            return bucket_name, object_key
            
        # If we couldn't extract bucket and key, raise an error
        else:
            raise ValidationError("Invalid event: Could not extract bucket and key")
            
    except KeyError as e:
        raise ValidationError(f"Invalid event structure: {str(e)}")
    except Exception as e:
        if not isinstance(e, ValidationError):
            raise ValidationError(f"Error validating event: {str(e)}")
        raise

def validate_file(bucket_name, object_key):
    """
    Validate that the file exists and has an appropriate content type and size.
    
    Args:
        bucket_name (str): S3 bucket name
        object_key (str): S3 object key
        
    Returns:
        bool: True if the file is valid
        
    Raises:
        ValidationError: If the file is invalid
    """
    logger.info(f"Validating file: bucket={bucket_name}, key={object_key}")
    
    try:
        # Create S3 client
        s3_client = boto3.client('s3')
        
        # Check if the object exists
        try:
            response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"File exists: {object_key}")
            
            # Check content type
            content_type = response.get('ContentType', '')
            logger.info(f"Content type: {content_type}")
            
            # Check file size
            file_size = response.get('ContentLength', 0)
            logger.info(f"File size: {file_size} bytes")
            
            if file_size == 0:
                raise ValidationError("File is empty (0 bytes)")
                
            # Check if it's a PDF (if the key ends with .pdf)
            if object_key.lower().endswith('.pdf'):
                is_pdf = content_type.lower() in ['application/pdf', 'binary/octet-stream']
                if not is_pdf:
                    logger.warning(f"File has PDF extension but content type is {content_type}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                raise ValidationError(f"File not found: {object_key}")
            elif error_code == '403':
                raise ValidationError(f"Access denied to file: {object_key}")
            else:
                raise ValidationError(f"Error accessing file: {str(e)}")
                
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Error validating file: {str(e)}")

def is_valid_json(json_str):
    """
    Check if a string is valid JSON.
    
    Args:
        json_str (str): The string to check
        
    Returns:
        bool: True if the string is valid JSON, False otherwise
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False

def validate_json_format(json_str):
    """
    Validate that a string is valid JSON.
    
    Args:
        json_str (str): The string to validate
        
    Returns:
        dict: The parsed JSON
        
    Raises:
        ValidationError: If the string is not valid JSON
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")

def validate_analysis_result(result):
    """
    Validate the analysis result from Bedrock.
    
    Args:
        result (dict): The analysis result to validate
        
    Returns:
        dict: The validated result
        
    Raises:
        ValidationError: If the result is invalid
    """
    required_fields = ['executive_summary', 'quality_rating', 'controls']
    
    # Check if result is a dictionary
    if not isinstance(result, dict):
        raise ValidationError(f"Analysis result must be a dictionary, got {type(result)}")
    
    # Check for required fields
    for field in required_fields:
        if field not in result:
            raise ValidationError(f"Analysis result missing required field: {field}")
    
    # Validate quality rating
    if not isinstance(result['quality_rating'], (int, float)):
        raise ValidationError(f"Quality rating must be a number, got {type(result['quality_rating'])}")
    
    if result['quality_rating'] < 1 or result['quality_rating'] > 5:
        raise ValidationError(f"Quality rating must be between 1 and 5, got {result['quality_rating']}")
    
    # Validate controls
    if not isinstance(result['controls'], list):
        raise ValidationError(f"Controls must be a list, got {type(result['controls'])}")
    
    return result 