"""
Lambda function to configure S3 bucket notifications.
This is used as a custom resource in CloudFormation to avoid circular dependencies.
"""

import json
import logging
import boto3
import cfnresponse
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function handler for the custom resource.
    
    Args:
        event (dict): Lambda event
        context (object): Lambda context
        
    Returns:
        None
    """
    logger.info('Received event: %s', json.dumps(event))
    
    # Get request type
    request_type = event['RequestType']
    
    try:
        if request_type == 'Create' or request_type == 'Update':
            # Get properties
            props = event['ResourceProperties']
            bucket_name = props['BucketName']
            notification_configuration = props['NotificationConfiguration']
            
            # Configure bucket notifications
            logger.info('Configuring bucket notifications for %s', bucket_name)
            s3 = boto3.client('s3')
            response = s3.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration=notification_configuration
            )
            logger.info('Successfully configured bucket notifications')
            
            # Send success response
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                'Message': f'Successfully configured bucket notifications for {bucket_name}'
            })
            
        elif request_type == 'Delete':
            # Get properties
            props = event['ResourceProperties']
            bucket_name = props['BucketName']
            
            # Remove bucket notifications
            logger.info('Removing bucket notifications for %s', bucket_name)
            s3 = boto3.client('s3')
            response = s3.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration={}
            )
            logger.info('Successfully removed bucket notifications')
            
            # Send success response
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {
                'Message': f'Successfully removed bucket notifications for {bucket_name}'
            })
            
        else:
            # Invalid request type
            logger.error('Invalid request type: %s', request_type)
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                'Message': f'Invalid request type: {request_type}'
            })
            
    except Exception as e:
        # Log error
        logger.error('Error: %s', str(e))
        logger.error(traceback.format_exc())
        
        # Send failure response
        cfnresponse.send(event, context, cfnresponse.FAILED, {
            'Message': f'Error: {str(e)}'
        }) 