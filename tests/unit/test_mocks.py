import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Import the services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda'))
from services.s3_service import S3Service
from services.textract_service import TextractService
from services.bedrock_service import BedrockService
from services.ses_service import SESService

class TestMocks:
    """Test cases for mocking AWS services."""
    
    @patch('boto3.client')
    def test_s3_service_mock(self, mock_boto3_client):
        """Test that S3Service can be mocked."""
        # Configure the mock
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client
        
        # Mock get_object response
        mock_body = MagicMock()
        mock_body.read.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_s3_client.get_object.return_value = {'Body': mock_body}
        
        # Create the service
        s3_service = S3Service()
        
        # Call the method
        result = s3_service.get_object('test-bucket', 'test-key.pdf')
        
        # Verify the result
        assert result == b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_s3_client.get_object.assert_called_once_with(Bucket='test-bucket', Key='test-key.pdf')
    
    @patch('boto3.client')
    def test_textract_service_mock(self, mock_boto3_client):
        """Test that TextractService can be mocked."""
        # Configure the mock
        mock_textract_client = MagicMock()
        mock_boto3_client.return_value = mock_textract_client
        
        # Mock detect_document_text response
        mock_textract_client.detect_document_text.return_value = {
            'Blocks': [
                {'BlockType': 'LINE', 'Text': 'Line 1'},
                {'BlockType': 'LINE', 'Text': 'Line 2'},
                {'BlockType': 'WORD', 'Text': 'Word'}  # This should be ignored
            ]
        }
        
        # Create the service
        textract_service = TextractService()
        
        # Call the method
        result = textract_service._extract_text_sync(b'%PDF-1.7\nTest PDF content\n%%EOF')
        
        # Verify the result
        assert result == 'Line 1\nLine 2\n'
        mock_textract_client.detect_document_text.assert_called_once()
    
    @patch('boto3.client')
    def test_bedrock_service_mock(self, mock_boto3_client):
        """Test that BedrockService can be mocked."""
        # Configure the mock
        mock_bedrock_client = MagicMock()
        mock_boto3_client.return_value = mock_bedrock_client
        
        # Mock invoke_model response
        mock_response = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = '{"content": [{"text": "{\\"Report Overview\\": {\\"Service Organization name\\": \\"Test Org\\"}}"}]}'
        mock_response.get.return_value = mock_body
        mock_bedrock_client.invoke_model.return_value = mock_response
        
        # Create the service
        bedrock_service = BedrockService()
        
        # Call the method
        result = bedrock_service._invoke_model("Test prompt")
        
        # Verify the result
        assert '{"Report Overview": {"Service Organization name": "Test Org"}}' in result
        mock_bedrock_client.invoke_model.assert_called_once()
    
    @patch('boto3.client')
    def test_ses_service_mock(self, mock_boto3_client):
        """Test that SESService can be mocked."""
        # Configure the mock
        mock_ses_client = MagicMock()
        mock_boto3_client.return_value = mock_ses_client
        
        # Mock send_raw_email response
        mock_ses_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        
        # Create the service
        ses_service = SESService()
        
        # Call the method
        result = ses_service.send_notification(
            'test@example.com',
            'Test Subject',
            {'Report Overview': {'Service Organization name': 'Test Org'}},
            'https://example.com/test-url'
        )
        
        # Verify the result
        assert result['MessageId'] == 'test-message-id'
        mock_ses_client.send_raw_email.assert_called_once() 