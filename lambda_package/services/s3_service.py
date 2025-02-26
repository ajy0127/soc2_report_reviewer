"""
S3 service module for the SOC2 Report Reviewer application.

This module provides functions for interacting with AWS S3, including:
- Retrieving objects from S3 buckets with enhanced error handling
- Storing analysis results as JSON in S3
- Tagging PDF files in S3 for tracking processing status

The module implements retry logic for resilience against transient AWS errors
and provides detailed logging for troubleshooting S3-related issues.
"""

import json
import logging
import boto3
import urllib.parse
import os
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from utils.error_handling import S3Error, retry

logger = logging.getLogger()

@retry(max_attempts=3, exceptions=(ClientError,))
def store_analysis(bucket, key, analysis_result):
    """
    Store analysis result as JSON in S3.
    
    This function converts the analysis result dictionary to a formatted JSON string
    and stores it in the specified S3 bucket with the appropriate content type.
    The function includes retry logic to handle transient AWS errors.
    
    Args:
        bucket (str): S3 bucket name where the analysis will be stored
        key (str): S3 object key (path) for the analysis JSON file
        analysis_result (dict): Analysis result dictionary to store
        
    Raises:
        S3Error: If there's an error storing the analysis after retry attempts
    """
    try:
        s3_client = boto3.client('s3')
        
        # Convert analysis result to formatted JSON with indentation for readability
        analysis_json = json.dumps(analysis_result, indent=2)
        
        # Store in S3 with appropriate content type for JSON
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=analysis_json,
            ContentType='application/json'
        )
        
        logger.info(f"Analysis stored at s3://{bucket}/{key}")
        
    except ClientError as e:
        error_message = f"Error storing analysis in S3: {str(e)}"
        logger.error(error_message)
        raise S3Error(error_message)

# Alias for store_analysis to match the import in the Lambda handler
# This allows the Lambda handler to use a more generic function name
store_result = store_analysis

@retry(max_attempts=3, exceptions=(ClientError,))
def tag_pdf(bucket, key, tag_key, tag_value):
    """
    Tag a PDF in S3 to track processing status or other metadata.
    
    This function retrieves existing tags for the object, adds or updates
    the specified tag, and writes the updated tag set back to the object.
    The function includes retry logic to handle transient AWS errors.
    
    Args:
        bucket (str): S3 bucket name containing the PDF
        key (str): S3 object key (path) for the PDF file
        tag_key (str): Tag key to add or update (e.g., "Status")
        tag_value (str): Tag value to set (e.g., "Analyzed")
        
    Raises:
        S3Error: If there's an error tagging the PDF after retry attempts
    """
    try:
        s3_client = boto3.client('s3')
        
        # Get existing tags - we want to preserve any existing tags on the object
        try:
            existing_tags_response = s3_client.get_object_tagging(
                Bucket=bucket,
                Key=key
            )
            existing_tags = existing_tags_response.get('TagSet', [])
        except ClientError:
            # If there's an error getting tags, assume no tags exist
            logger.info(f"No existing tags found for s3://{bucket}/{key}")
            existing_tags = []
        
        # Add or update the tag in the existing tag set
        tag_exists = False
        for tag in existing_tags:
            if tag['Key'] == tag_key:
                tag['Value'] = tag_value
                tag_exists = True
                logger.info(f"Updated existing tag {tag_key}={tag_value}")
                break
        
        if not tag_exists:
            existing_tags.append({
                'Key': tag_key,
                'Value': tag_value
            })
            logger.info(f"Added new tag {tag_key}={tag_value}")
        
        # Put the updated tags back on the object
        s3_client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={
                'TagSet': existing_tags
            }
        )
        
        logger.info(f"Tagged PDF at s3://{bucket}/{key} with {tag_key}={tag_value}")
        
    except ClientError as e:
        error_message = f"Error tagging PDF in S3: {str(e)}"
        logger.error(error_message)
        raise S3Error(error_message)

@retry(max_attempts=3, exceptions=(ClientError,))
def get_s3_object(bucket, key):
    """
    Retrieve an object from S3 with enhanced error handling and debugging.
    
    This function includes extensive error handling and debugging to help
    troubleshoot S3 access issues, including:
    - URL decoding of the object key
    - Checking if the object exists when retrieval fails
    - Listing similar objects to help identify key errors
    - Logging IAM identity information for permission issues
    
    The function includes retry logic to handle transient AWS errors.
    
    Args:
        bucket (str): S3 bucket name containing the object
        key (str): S3 object key (path) to retrieve
        
    Returns:
        dict: S3 GetObject response containing the object data and metadata
        
    Raises:
        S3Error: If there's an error retrieving the object after retry attempts
    """
    # Log the exact key being used for debugging purposes
    logger.info(f"Attempting to access S3 object - Bucket: {bucket}")
    logger.info(f"Original Key: {key}")
    
    # Handle URL encoding properly - S3 keys in events are often URL encoded
    try:
        decoded_key = urllib.parse.unquote_plus(key)
        logger.info(f"Decoded Key: {decoded_key}")
    except Exception as e:
        logger.warning(f"Error decoding key: {str(e)}")
        decoded_key = key
    
    # Create S3 client with explicit region and retry configuration
    # This ensures consistent behavior regardless of Lambda environment settings
    region = os.environ.get('AWS_REGION', 'us-east-1')
    s3_client = boto3.client('s3', region_name=region, config=Config(
        retries={'max_attempts': 3, 'mode': 'standard'},
        connect_timeout=5,  # 5 seconds for connection timeout
        read_timeout=60     # 60 seconds for read timeout (for large files)
    ))
    
    try:
        # Try to access the object
        response = s3_client.get_object(Bucket=bucket, Key=decoded_key)
        logger.info(f"S3 object retrieved successfully - Size: {response.get('ContentLength', 'Unknown')} bytes, Type: {response.get('ContentType', 'Unknown')}")
        return response
    except Exception as e:
        logger.error(f"Error accessing S3 object: {str(e)}")
        
        # Enhanced error handling to help troubleshoot the issue
        
        # Check if the object exists but can't be accessed (permissions issue)
        try:
            s3_client.head_object(Bucket=bucket, Key=decoded_key)
            logger.info("Object exists but couldn't be retrieved - likely permissions issue")
        except Exception as head_error:
            logger.error(f"Error checking if object exists: {str(head_error)}")
            if '404' in str(head_error):
                logger.error("Object doesn't exist - check the key path")
            elif '403' in str(head_error):
                logger.error("Access denied to object - check IAM permissions")
                
                # Get caller identity for debugging IAM issues
                try:
                    sts_client = boto3.client('sts')
                    identity = sts_client.get_caller_identity()
                    logger.info(f"Lambda executing as: {identity['Arn']}")
                except Exception as sts_error:
                    logger.error(f"Error getting caller identity: {str(sts_error)}")
        
        # Try listing objects with similar prefix to help identify key errors
        prefix = '/'.join(decoded_key.split('/')[:-1]) if '/' in decoded_key else ''
        logger.info(f"Listing objects with prefix: {prefix}")
        try:
            objects = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)
            if 'Contents' in objects and objects.get('KeyCount', 0) > 0:
                logger.info(f"Found {len(objects['Contents'])} objects with similar prefix")
                for obj in objects['Contents'][:5]:  # Log first 5 similar objects
                    logger.info(f"Similar object: {obj['Key']}")
            else:
                logger.warning(f"No objects found with prefix: {prefix}")
                
                # Try listing bucket root as a fallback to check bucket access
                root_objects = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=5)
                if 'Contents' in root_objects and root_objects.get('KeyCount', 0) > 0:
                    logger.info(f"Found {root_objects.get('KeyCount', 0)} objects in bucket root")
                    for obj in root_objects['Contents'][:5]:
                        logger.info(f"Root object: {obj['Key']}")
                else:
                    logger.warning("No objects found in bucket root - check bucket name and permissions")
        except Exception as list_err:
            logger.error(f"Error listing similar objects: {str(list_err)}")
        
        # Raise an informative error with the full S3 URI
        error_message = f"Error accessing S3 object s3://{bucket}/{decoded_key}: {str(e)}"
        logger.error(error_message)
        raise S3Error(error_message)

# Alias for get_s3_object to match the import in the Lambda handler
# This allows the Lambda handler to use a more generic function name
get_object = get_s3_object 