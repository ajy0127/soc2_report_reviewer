import boto3
import logging
import time
from botocore.exceptions import ClientError

logger = logging.getLogger()

class TextractService:
    """
    Service class for Amazon Textract operations.
    
    This class provides methods for extracting text from PDF documents using
    Amazon Textract. It handles both synchronous and asynchronous text extraction
    based on the size of the document.
    """
    
    def __init__(self):
        """
        Initialize the Textract service with boto3 client.
        
        Creates a Textract client using boto3, which will use the AWS credentials
        from the Lambda execution environment.
        """
        self.textract_client = boto3.client('textract')
    
    def extract_text(self, pdf_content):
        """
        Extracts text from a PDF document using Amazon Textract.
        
        This method serves as the main entry point for text extraction.
        It automatically chooses between synchronous and asynchronous APIs
        based on the size of the document:
        - For documents < 5MB: Uses synchronous API (faster, simpler)
        - For documents >= 5MB: Uses asynchronous API (required for larger files)
        
        Args:
            pdf_content (bytes): The PDF content as bytes
            
        Returns:
            str: The extracted text
            
        Raises:
            ClientError: If text extraction fails due to AWS service issues
        """
        try:
            logger.info("Starting text extraction with Textract")
            
            # Choose the appropriate API based on document size
            # Textract's synchronous API has a 5MB limit
            if len(pdf_content) < 5 * 1024 * 1024:  # 5MB limit for synchronous API
                return self._extract_text_sync(pdf_content)
            else:
                # For larger documents, use asynchronous API
                return self._extract_text_async(pdf_content)
                
        except ClientError as e:
            logger.error(f"Error extracting text with Textract: {str(e)}")
            raise
    
    def _extract_text_sync(self, pdf_content):
        """
        Extracts text using Textract's synchronous API.
        
        This method is used for smaller documents (< 5MB) and provides
        immediate results without the need for polling.
        
        Args:
            pdf_content (bytes): The PDF content
            
        Returns:
            str: The extracted text
        """
        # Call the synchronous Textract API
        response = self.textract_client.detect_document_text(
            Document={'Bytes': pdf_content}
        )
        
        # Extract text from the response
        # Textract returns a list of "Blocks" of different types
        # We're only interested in LINE blocks which contain text lines
        text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text'] + "\n"
        
        logger.info(f"Extracted {len(text)} characters of text")
        return text
    
    def _extract_text_async(self, pdf_content):
        """
        Extracts text using Textract's asynchronous API.
        
        This method is used for larger documents (>= 5MB) and involves:
        1. Starting an asynchronous job
        2. Polling for job completion
        3. Retrieving results (potentially paginated)
        
        Args:
            pdf_content (bytes): The PDF content
            
        Returns:
            str: The extracted text
            
        Raises:
            Exception: If the Textract job fails
        """
        # Step 1: Start the text detection job
        response = self.textract_client.start_document_text_detection(
            DocumentLocation={'Bytes': pdf_content}
        )
        job_id = response['JobId']
        logger.info(f"Started async text extraction job: {job_id}")
        
        # Step 2: Wait for the job to complete
        # Poll the job status every 5 seconds until it's no longer IN_PROGRESS
        status = 'IN_PROGRESS'
        while status == 'IN_PROGRESS':
            time.sleep(5)  # Wait 5 seconds between polling attempts
            response = self.textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            logger.info(f"Text extraction job status: {status}")
        
        # Check if the job completed successfully
        if status != 'SUCCEEDED':
            error_message = response.get('StatusMessage', 'Unknown error')
            logger.error(f"Text extraction job failed: {error_message}")
            raise Exception(f"Textract job failed: {error_message}")
        
        # Step 3: Get all pages of results
        # Results may be paginated if the document is large
        pages = []
        next_token = None
        
        # Retrieve all pages of results using pagination
        while True:
            if next_token:
                response = self.textract_client.get_document_text_detection(
                    JobId=job_id,
                    NextToken=next_token
                )
            else:
                response = self.textract_client.get_document_text_detection(
                    JobId=job_id
                )
            
            pages.append(response)
            
            # Check if there are more pages
            if 'NextToken' in response:
                next_token = response['NextToken']
            else:
                break
        
        # Extract text from all pages of results
        text = ""
        for page in pages:
            for item in page['Blocks']:
                if item['BlockType'] == 'LINE':
                    text += item['Text'] + "\n"
        
        logger.info(f"Extracted {len(text)} characters of text")
        return text 