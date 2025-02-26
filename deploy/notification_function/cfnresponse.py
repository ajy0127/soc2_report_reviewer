"""
Send a response to CloudFormation custom resource.
"""

import json
import logging
import urllib.request

# Response status constants
SUCCESS = "SUCCESS"
FAILED = "FAILED"

logger = logging.getLogger()

def send(event, context, response_status, response_data, physical_resource_id=None, no_echo=False):
    """
    Send a response to CloudFormation regarding the success or failure of a custom resource deployment.
    
    Args:
        event (dict): The CloudFormation custom resource request
        context (obj): The Lambda context
        response_status (str): SUCCESS or FAILED
        response_data (dict): The response data to send back
        physical_resource_id (str, optional): The physical resource ID
        no_echo (bool, optional): Whether to mask the response in CloudFormation console
        
    Returns:
        None
    """
    response_url = event['ResponseURL']

    logger.info(f"CFN response URL: {response_url}")

    response_body = {
        'Status': response_status,
        'Reason': f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        'PhysicalResourceId': physical_resource_id or context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'NoEcho': no_echo,
        'Data': response_data
    }

    json_response_body = json.dumps(response_body)
    
    logger.info(f"Response body: {json_response_body}")

    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }

    try:
        req = urllib.request.Request(response_url,
                                     data=json_response_body.encode('utf-8'),
                                     headers=headers,
                                     method='PUT')
        
        response = urllib.request.urlopen(req)
        logger.info(f"Status code: {response.getcode()}")
        logger.info(f"Status message: {response.msg}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending response: {str(e)}")
        return False 