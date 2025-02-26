"""
Error handling utilities for the SOC 2 Report Analysis Tool.
"""

import logging
import traceback
import json
from functools import wraps
import time

logger = logging.getLogger()

class ProcessingError(Exception):
    """Base exception for processing errors."""
    pass

class TextractError(ProcessingError):
    """Exception for Textract-related errors."""
    pass

class BedrockError(ProcessingError):
    """Exception for Bedrock-related errors."""
    pass

class S3Error(ProcessingError):
    """Exception for S3-related errors."""
    pass

class SESError(ProcessingError):
    """Exception for SES-related errors."""
    pass

class ValidationError(ProcessingError):
    """Exception for validation errors."""
    pass

def handle_exceptions(func):
    """
    Decorator to handle exceptions in Lambda functions.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ProcessingError as e:
            logger.error(f"Processing error: {str(e)}", exc_info=True)
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': str(e),
                    'type': e.__class__.__name__
                })
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': str(e),
                    'trace': traceback.format_exc()
                })
            }
    return wrapper

def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts (int): Maximum number of attempts
        delay (float): Initial delay between retries in seconds
        backoff (float): Backoff multiplier
        exceptions (tuple): Exceptions to catch and retry
        
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    attempt += 1
                    current_delay *= backoff
        return wrapper
    return decorator 