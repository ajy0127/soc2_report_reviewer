import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import json
import subprocess
import tempfile
import PyPDF2

# Import the services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda'))
from services.s3_service import S3Service
from services.ocrmypdf_service import OCRmyPDFService
from services.bedrock_service import BedrockService
from services.ses_service import SESService

class TestMocks(unittest.TestCase):
    """Test cases for mocking AWS services."""
    
    @patch('boto3.client')
    def test_s3_service_mock(self, mock_boto3):
        """Test the S3Service mock."""
        # Configure the mock
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        
        # Configure get_object response
        mock_response = {
            'Body': MagicMock()
        }
        mock_response['Body'].read.return_value = b'Test PDF content'
        mock_s3.get_object.return_value = mock_response

        # Create the service and call get_object
        service = S3Service()
        result = service.get_object('test-bucket', 'test-key.pdf')

        # Verify the result
        self.assertEqual(result, b'Test PDF content')
        mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='test-key.pdf'
        )
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('PyPDF2.PdfReader')
    def test_ocrmypdf_service_mock(self, mock_pdf_reader, mock_exists, mock_subprocess):
        """Test the OCRmyPDFService mock."""
        from services.ocrmypdf_service import OCRmyPDFService

        # Configure mocks
        mock_process = MagicMock()
        mock_process.stdout = "OCRmyPDF 14.0.0"
        mock_subprocess.return_value = mock_process
        
        # Configure os.path.exists to return True for the PDF file
        mock_exists.return_value = True
        
        # Configure PyPDF2.PdfReader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted text from PDF"
        mock_pdf_reader.return_value.pages = [mock_page]

        # Create the service and call extract_text
        service = OCRmyPDFService()
        result = service.extract_text(b'%PDF-1.7\nTest PDF content\n%%EOF')

        # Verify the result - account for page formatting in the output
        self.assertIn("Extracted text from PDF", result)
        
        # Verify subprocess.run was called with the correct arguments
        mock_subprocess.assert_any_call(["ocrmypdf", "--version"], capture_output=True, text=True)
        
        # Verify that PyPDF2.PdfReader was used to extract text
        mock_pdf_reader.assert_called_once()
    
    @patch('boto3.client')
    def test_bedrock_service_mock(self, mock_boto3):
        """Test the BedrockService mock."""
        from services.bedrock_service import BedrockService

        # Configure the mock
        mock_bedrock = MagicMock()
        mock_boto3.return_value = mock_bedrock
        
        # Configure invoke_model response with a structure that will be parsed correctly
        mock_response = {
            'body': MagicMock()
        }
        # Create a response that matches what the service expects
        mock_response['body'].read.return_value = json.dumps({
            'content': [
                {
                    'type': 'text',
                    'text': json.dumps({
                        'Report Overview': {
                            'Service Organization name': 'Test Org',
                            'Service Auditor name': 'Test Auditor',
                            'Report Type': 'Type 2',
                            'Report Period': '2023-01-01 to 2023-12-31'
                        }
                    })
                }
            ]
        }).encode('utf-8')
        mock_bedrock.invoke_model.return_value = mock_response

        # Create the service and call analyze_soc2_report
        service = BedrockService()
        result = service.analyze_soc2_report('Extracted text from PDF')

        # Verify the result
        self.assertEqual(result['Report Overview']['Service Organization name'], 'Test Org')
        self.assertEqual(result['Report Overview']['Report Type'], 'Type 2')
        mock_bedrock.invoke_model.assert_called_once()
    
    @patch('boto3.client')
    def test_ses_service_mock(self, mock_boto3):
        """Test the SESService mock."""
        from services.ses_service import SESService

        # Configure the mock
        mock_ses = MagicMock()
        mock_boto3.return_value = mock_ses
        
        # Configure send_raw_email response
        mock_ses.send_raw_email.return_value = {
            'MessageId': 'test-message-id'
        }

        # Create the service and call send_notification
        service = SESService()
        analysis_result = {
            'Report Overview': {
                'Service Organization name': 'Test Org',
                'Service Auditor name': 'Test Auditor',
                'Report Type': 'Type 2',
                'Report Period': '2023-01-01 to 2023-12-31'
            }
        }
        result = service.send_notification('test@example.com', 'test-report.pdf', analysis_result, 'https://example.com/test-url')

        # Verify the result
        self.assertEqual(result['MessageId'], 'test-message-id')
        mock_ses.send_raw_email.assert_called_once()

if __name__ == '__main__':
    unittest.main() 