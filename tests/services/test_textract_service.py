"""
Tests for the Textract service.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Add the lambda_code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_code'))

# Import the Textract service
from textract_service import extract_text, extract_text_with_analyze_document, extract_text_async

class TestTextractService:
    """Test cases for the Textract service."""

    @patch('textract_service.boto3.client')
    def test_extract_text_success(self, mock_boto3_client, sample_textract_response):
        """Test the extract_text function with a successful response."""
        # Mock the Textract client
        mock_textract = MagicMock()
        mock_boto3_client.return_value = mock_textract
        
        # Mock the detect_document_text method
        mock_textract.detect_document_text.return_value = sample_textract_response
        
        # Call the extract_text function
        result = extract_text("test-bucket", "test-key.pdf")
        
        # Verify the result
        assert "SOC 2 Type 2 Report" in result
        assert "Control Environment" in result
        assert "The organization maintains a strong control environment." in result
        
        # Verify that the Textract client was called with the correct arguments
        mock_textract.detect_document_text.assert_called_once()

    @patch('textract_service.boto3.client')
    def test_extract_text_client_error(self, mock_boto3_client):
        """Test the extract_text function with a ClientError."""
        # Mock the Textract client
        mock_textract = MagicMock()
        mock_boto3_client.return_value = mock_textract
        
        # Mock the detect_document_text method to raise a ClientError
        error_response = {
            'Error': {
                'Code': 'InvalidS3ObjectException',
                'Message': 'Unable to get object metadata from S3'
            }
        }
        mock_textract.detect_document_text.side_effect = ClientError(
            error_response, 'DetectDocumentText')
        
        # Call the extract_text function and expect an exception
        from utils.error_handling import TextractError
        with pytest.raises(TextractError) as excinfo:
            extract_text("test-bucket", "test-key.pdf")
        
        # Verify the exception message
        assert "Unable to get object metadata from S3" in str(excinfo.value)

    @patch('textract_service.boto3.client')
    def test_extract_text_with_analyze_document_success(self, mock_boto3_client, sample_textract_response):
        """Test the extract_text_with_analyze_document function with a successful response."""
        # Mock the Textract client
        mock_textract = MagicMock()
        mock_boto3_client.return_value = mock_textract
        
        # Mock the analyze_document method
        mock_textract.analyze_document.return_value = sample_textract_response
        
        # Call the extract_text_with_analyze_document function
        result = extract_text_with_analyze_document("test-bucket", "test-key.pdf")
        
        # Verify the result
        assert "SOC 2 Type 2 Report" in result
        assert "Control Environment" in result
        assert "The organization maintains a strong control environment." in result
        
        # Verify that the Textract client was called with the correct arguments
        mock_textract.analyze_document.assert_called_once()

    @patch('textract_service.boto3.client')
    def test_extract_text_async_success(self, mock_boto3_client):
        """Test the extract_text_async function with a successful response."""
        # Mock the Textract client
        mock_textract = MagicMock()
        mock_boto3_client.return_value = mock_textract
        
        # Mock the start_document_text_detection method
        mock_textract.start_document_text_detection.return_value = {
            'JobId': 'test-job-id'
        }
        
        # Mock the get_document_text_detection method
        mock_textract.get_document_text_detection.return_value = {
            'JobStatus': 'SUCCEEDED',
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'SOC 2 Type 2 Report'
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Control Environment'
                }
            ]
        }
        
        # Call the extract_text_async function
        result = extract_text_async("test-bucket", "test-key.pdf")
        
        # Verify the result
        assert "SOC 2 Type 2 Report" in result
        assert "Control Environment" in result
        
        # Verify that the Textract client was called with the correct arguments
        mock_textract.start_document_text_detection.assert_called_once()
        mock_textract.get_document_text_detection.assert_called()

    @patch('textract_service.boto3.client')
    def test_extract_text_async_job_failed(self, mock_boto3_client):
        """Test the extract_text_async function with a failed job."""
        # Mock the Textract client
        mock_textract = MagicMock()
        mock_boto3_client.return_value = mock_textract
        
        # Mock the start_document_text_detection method
        mock_textract.start_document_text_detection.return_value = {
            'JobId': 'test-job-id'
        }
        
        # Mock the get_document_text_detection method to return a failed job
        mock_textract.get_document_text_detection.return_value = {
            'JobStatus': 'FAILED',
            'StatusMessage': 'Job failed due to an error'
        }
        
        # Call the extract_text_async function and expect an exception
        from utils.error_handling import TextractError
        with pytest.raises(TextractError) as excinfo:
            extract_text_async("test-bucket", "test-key.pdf")
        
        # Verify the exception message
        assert "Job failed due to an error" in str(excinfo.value) 