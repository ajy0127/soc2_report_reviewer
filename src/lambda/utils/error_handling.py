import json
import logging
from utils.validation import ValidationError

logger = logging.getLogger()

def handle_error(error):
    """
    Handles different types of errors and returns appropriate responses.
    
    This function maps different error types to appropriate HTTP status codes
    and formats error messages for the API response. It handles:
    - ValidationError (400 Bad Request)
    - Access Denied errors (403 Forbidden)
    - Resource Not Found errors (404 Not Found)
    - All other errors (500 Internal Server Error)
    
    Args:
        error (Exception): The exception that was raised
        
    Returns:
        dict: A response object with appropriate status code and error message
    """
    # Case 1: Validation errors (400 Bad Request)
    # These are client errors where the request is invalid
    if isinstance(error, ValidationError):
        logger.warning(f"Validation error: {str(error)}")
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': str(error),
                'type': 'ValidationError'
            })
        }
    
    # Case 2: Access denied errors (403 Forbidden)
    # These occur when the Lambda doesn't have permission to access a resource
    elif 'AccessDenied' in str(error):
        logger.error(f"Access denied error: {str(error)}")
        return {
            'statusCode': 403,
            'body': json.dumps({
                'error': 'Access denied to required resources',
                'type': 'AccessDeniedError'
            })
        }
    
    # Case 3: Resource not found errors (404 Not Found)
    # These occur when a requested resource doesn't exist
    elif 'ResourceNotFound' in str(error) or 'NoSuchKey' in str(error):
        logger.error(f"Resource not found error: {str(error)}")
        return {
            'statusCode': 404,
            'body': json.dumps({
                'error': 'The requested resource was not found',
                'type': 'ResourceNotFoundError'
            })
        }
    
    # Case 4: All other errors (500 Internal Server Error)
    # These are unexpected errors that should be investigated
    else:
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'An unexpected error occurred',
                'type': 'InternalServerError'
            })
        } 