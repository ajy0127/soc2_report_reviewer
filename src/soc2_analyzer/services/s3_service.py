"""
S3 service for the SOC 2 Report Analysis Tool.
"""

import json
import logging
import boto3
from botocore.exceptions import ClientError
from soc2_analyzer.utils.error_handling import S3Error, retry

logger = logging.getLogger()

@retry(max_attempts=3, exceptions=(ClientError,))
def store_analysis(bucket, key, analysis_result):
    """
    Store analysis result as JSON in S3.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        analysis_result (dict): Analysis result to store
        
    Raises:
        S3Error: If there's an error storing the analysis
    """
    try:
        s3_client = boto3.client('s3')
        
        # Convert analysis result to JSON
        analysis_json = json.dumps(analysis_result, indent=2)
        
        # Store in S3
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

@retry(max_attempts=3, exceptions=(ClientError,))
def tag_pdf(bucket, key, tag_key, tag_value):
    """
    Tag a PDF in S3.
    
    Args:
        bucket (str): S3 bucket name
        key (str): S3 object key
        tag_key (str): Tag key
        tag_value (str): Tag value
        
    Raises:
        S3Error: If there's an error tagging the PDF
    """
    try:
        s3_client = boto3.client('s3')
        
        # Get existing tags
        try:
            existing_tags_response = s3_client.get_object_tagging(
                Bucket=bucket,
                Key=key
            )
            existing_tags = existing_tags_response.get('TagSet', [])
        except ClientError:
            # If there's an error getting tags, assume no tags
            existing_tags = []
        
        # Add or update the tag
        tag_exists = False
        for tag in existing_tags:
            if tag['Key'] == tag_key:
                tag['Value'] = tag_value
                tag_exists = True
                break
        
        if not tag_exists:
            existing_tags.append({
                'Key': tag_key,
                'Value': tag_value
            })
        
        # Put the updated tags
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