import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger()

class S3Service:
    """
    Service class for S3 operations.
    
    This class provides methods for interacting with Amazon S3, including:
    - Retrieving objects from S3
    - Uploading objects to S3
    - Generating presigned URLs for temporary access to S3 objects
    """
    
    def __init__(self):
        """
        Initialize the S3 service with boto3 client.
        
        Creates an S3 client using boto3, which will use the AWS credentials
        from the Lambda execution environment.
        """
        self.s3_client = boto3.client('s3')
    
    def get_object(self, bucket_name, object_key):
        """
        Retrieves an object from S3.
        
        This method downloads the content of an S3 object as bytes.
        It's used to retrieve PDF files for processing.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            object_key (str): The key of the object in the bucket
            
        Returns:
            bytes: The content of the object
            
        Raises:
            ClientError: If the object cannot be retrieved (e.g., doesn't exist or no permission)
        """
        try:
            logger.info(f"Retrieving object {object_key} from bucket {bucket_name}")
            
            # Call the S3 API to get the object
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            
            # Read the object body as bytes
            return response['Body'].read()
        except ClientError as e:
            # Log the error and re-raise it for handling upstream
            logger.error(f"Error retrieving object from S3: {str(e)}")
            raise
    
    def put_object(self, bucket_name, object_key, content):
        """
        Puts an object into S3.
        
        This method uploads content to an S3 bucket with the specified key.
        It's used to store analysis results in the output bucket.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            object_key (str): The key of the object in the bucket
            content (str or bytes): The content to upload
            
        Returns:
            dict: The response from S3
            
        Raises:
            ClientError: If the object cannot be uploaded (e.g., no permission)
        """
        try:
            logger.info(f"Uploading object to {object_key} in bucket {bucket_name}")
            
            # Call the S3 API to put the object
            response = self.s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=content
            )
            return response
        except ClientError as e:
            # Log the error and re-raise it for handling upstream
            logger.error(f"Error uploading object to S3: {str(e)}")
            raise
    
    def generate_presigned_url(self, bucket_name, object_key, expiration=3600):
        """
        Generates a presigned URL for an S3 object.
        
        This method creates a temporary URL that allows access to an S3 object
        without requiring AWS credentials. The URL expires after the specified time.
        It's used to provide access to analysis results in emails.
        
        Args:
            bucket_name (str): The name of the S3 bucket
            object_key (str): The key of the object in the bucket
            expiration (int): The time in seconds for the URL to remain valid (default: 1 hour)
            
        Returns:
            str: The presigned URL
            
        Raises:
            ClientError: If the URL cannot be generated
        """
        try:
            logger.info(f"Generating presigned URL for {object_key} in bucket {bucket_name}")
            
            # Generate a presigned URL for the S3 object
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            # Log the error and re-raise it for handling upstream
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise 