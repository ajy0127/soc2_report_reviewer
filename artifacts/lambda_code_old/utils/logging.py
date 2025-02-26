"""
Logging utilities for the SOC 2 Report Analysis Tool.
"""

import logging
import os
import json

def setup_logging():
    """
    Set up logging configuration.
    
    Returns:
        logging.Logger: Configured logger
    """
    # Get the log level from environment variable or default to INFO
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicate logs in Lambda
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    # Create a new handler
    handler = logging.StreamHandler()
    
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    # Set the formatter on the handler
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    return logger

def log_event(logger, event, level=logging.INFO):
    """
    Log an event with appropriate redaction of sensitive information.
    
    Args:
        logger (logging.Logger): Logger to use
        event (dict): Event to log
        level (int): Logging level
    """
    # Create a copy of the event to avoid modifying the original
    event_copy = event.copy() if isinstance(event, dict) else event
    
    # Redact sensitive information if present
    if isinstance(event_copy, dict):
        redact_sensitive_info(event_copy)
    
    # Log the event
    logger.log(level, f"Event: {json.dumps(event_copy, default=str)}")

def redact_sensitive_info(obj):
    """
    Recursively redact sensitive information in a dictionary.
    
    Args:
        obj (dict): Dictionary to redact
    """
    sensitive_keys = [
        'password', 'secret', 'key', 'token', 'credential',
        'authorization', 'auth', 'apikey', 'api_key'
    ]
    
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            # Check if the key contains sensitive information
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                obj[key] = '[REDACTED]'
            elif isinstance(obj[key], (dict, list)):
                redact_sensitive_info(obj[key])
    
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                redact_sensitive_info(item)

def log_error(logger, message, exception=None):
    """
    Log an error message with exception details if provided.
    
    Args:
        logger (logging.Logger): Logger to use
        message (str): Error message
        exception (Exception, optional): Exception to log
    """
    if exception:
        logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        logger.error(message) 