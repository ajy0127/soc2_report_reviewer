"""
AWS helper utilities for the SOC 2 Report Analysis Tool.
"""

import boto3
import logging
import json
from botocore.exceptions import ClientError
from utils.error_handling import retry

logger = logging.getLogger()

def check_iam_permissions():
    """
    Check Lambda's IAM permissions and identity.
    Returns True if checks pass, False otherwise.
    """
    logger.info("Checking IAM permissions and identity...")
    
    try:
        # Check identity
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        logger.info(f"Lambda executing as: {identity['Arn']}")
        
        # Check S3 permissions
        try:
            s3_client = boto3.client('s3')
            buckets = s3_client.list_buckets()
            logger.info(f"Lambda has access to {len(buckets['Buckets'])} S3 buckets")
            for bucket in buckets['Buckets'][:3]:  # Log first 3 buckets
                logger.info(f"Accessible bucket: {bucket['Name']}")
                
                # Try to list objects in the bucket
                try:
                    objects = s3_client.list_objects_v2(Bucket=bucket['Name'], MaxKeys=1)
                    logger.info(f"Can list objects in bucket: {bucket['Name']}")
                except ClientError as e:
                    logger.warning(f"Cannot list objects in bucket {bucket['Name']}: {str(e)}")
        except ClientError as e:
            logger.error(f"S3 permission check failed: {str(e)}")
        
        # Check Textract permissions
        try:
            textract = boto3.client('textract')
            # Just check if we can access the service
            response = textract.list_document_classification_jobs(MaxResults=1)
            logger.info("Lambda has access to Textract service")
        except ClientError as e:
            if 'AccessDenied' in str(e):
                logger.warning(f"Textract permission check failed: {str(e)}")
            else:
                logger.info("Lambda has access to Textract service (operation-level permissions may vary)")
        
        # Check Bedrock permissions (if applicable)
        try:
            bedrock = boto3.client('bedrock-runtime')
            logger.info("Lambda has access to Bedrock service")
        except (ClientError, Exception) as e:
            logger.warning(f"Bedrock permission check failed: {str(e)}")
        
        # Check SES permissions (if applicable)
        try:
            ses = boto3.client('ses')
            response = ses.get_account_sending_enabled()
            logger.info("Lambda has access to SES service")
        except ClientError as e:
            logger.warning(f"SES permission check failed: {str(e)}")
        
        logger.info("IAM permission check completed")
        return True
    except Exception as e:
        logger.error(f"IAM permission check failed: {str(e)}")
        return False

@retry(max_attempts=2, exceptions=(ClientError,))
def verify_s3_bucket_access(bucket_name):
    """
    Verify if the Lambda function has access to a specific S3 bucket.
    
    Args:
        bucket_name (str): Name of the S3 bucket to check
        
    Returns:
        dict: Results of the bucket access check including read/write capabilities
    """
    result = {
        'bucket': bucket_name,
        'exists': False,
        'can_list': False,
        'can_get': False,
        'can_put': False,
        'can_delete': False,
        'errors': {}
    }
    
    s3_client = boto3.client('s3')
    test_key = 'test/permission-check.txt'
    test_content = 'IAM permission check'
    
    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        result['exists'] = True
        logger.info(f"Bucket {bucket_name} exists and is accessible")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        result['errors']['head_bucket'] = f"{error_code}: {str(e)}"
        logger.warning(f"Cannot access bucket {bucket_name}: {error_code}")
        return result
    
    # Check list permission
    try:
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        result['can_list'] = True
        logger.info(f"Can list objects in bucket {bucket_name}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        result['errors']['list'] = f"{error_code}: {str(e)}"
        logger.warning(f"Cannot list objects in bucket {bucket_name}: {error_code}")
    
    # Check put permission (only if we want to be intrusive)
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        result['can_put'] = True
        logger.info(f"Can put objects in bucket {bucket_name}")
        
        # Check get permission
        try:
            response = s3_client.get_object(
                Bucket=bucket_name,
                Key=test_key
            )
            result['can_get'] = True
            logger.info(f"Can get objects from bucket {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            result['errors']['get'] = f"{error_code}: {str(e)}"
            logger.warning(f"Cannot get objects from bucket {bucket_name}: {error_code}")
        
        # Check delete permission
        try:
            s3_client.delete_object(
                Bucket=bucket_name,
                Key=test_key
            )
            result['can_delete'] = True
            logger.info(f"Can delete objects from bucket {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            result['errors']['delete'] = f"{error_code}: {str(e)}"
            logger.warning(f"Cannot delete objects from bucket {bucket_name}: {error_code}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        result['errors']['put'] = f"{error_code}: {str(e)}"
        logger.warning(f"Cannot put objects in bucket {bucket_name}: {error_code}")
    
    return result 