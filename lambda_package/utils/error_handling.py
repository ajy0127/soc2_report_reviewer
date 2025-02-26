"""
Error handling utilities for the SOC2 Report Reviewer application.
"""

import logging
import json
import traceback

logger = logging.getLogger()

class ServiceError(Exception):
    """Base exception for all service-related errors."""
    def __init__(self, message, status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_type = self.__class__.__name__

class ValidationError(ServiceError):
    """Exception for validation errors."""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)

class S3Error(ServiceError):
    """Exception for S3-related errors."""
    pass

class TextractError(ServiceError):
    """Exception for Textract-related errors."""
    pass

class BedrockError(ServiceError):
    """Exception for Bedrock-related errors."""
    pass

class SESError(ServiceError):
    """Exception for SES-related errors."""
    pass

def handle_error(error, context=None):
    """
    Handle service errors and return a formatted response.
    
    Args:
        error (ServiceError): The error to handle
        context (dict, optional): Additional context information
        
    Returns:
        dict: Formatted error response
    """
    # Log the error
    error_type = error.error_type if hasattr(error, 'error_type') else type(error).__name__
    error_message = str(error)
    status_code = error.status_code if hasattr(error, 'status_code') else 500
    details = error.details if hasattr(error, 'details') else {}
    
    # Merge additional context if provided
    if context:
        details.update(context)
    
    # Log error details
    logger.error(f"Error type: {error_type}")
    logger.error(f"Error message: {error_message}")
    if details:
        logger.error(f"Error details: {json.dumps(details)}")
    
    # Return formatted response
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'error': error_message,
            'type': error_type,
            'details': details
        })
    }

def retry(func=None, max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator with exponential backoff.
    
    Args:
        func (callable, optional): The function to decorate
        max_attempts (int): Maximum number of attempts
        delay (float): Initial delay between retries in seconds
        backoff (float): Backoff multiplier
        exceptions (tuple): Exceptions to catch and retry
        
    Returns:
        callable: The decorated function
    """
    import time
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    attempt += 1
                    current_delay *= backoff
        return wrapper
    
    if func:
        return decorator(func)
    return decorator 