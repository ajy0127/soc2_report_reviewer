import json
import os
import unittest
from unittest.mock import patch, MagicMock

# Set environment variables for testing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['INPUT_BUCKET'] = 'test-input-bucket'
os.environ['OUTPUT_BUCKET'] = 'test-output-bucket'
os.environ['NOTIFICATION_EMAIL'] = 'test@example.com'
os.environ['BEDROCK_MODEL_ID'] = 'test-model-id'
os.environ['ENVIRONMENT'] = 'test'

# Import the Lambda handler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda'))
from utils.validation import ValidationError

# Use patch to mock the services before importing app
with patch('boto3.client'):
    from app import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    """Test cases for the Lambda handler function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock event
        self.event = {
            'Records': [
                {
                    'eventSource': 'aws:s3',
                    's3': {
                        'bucket': {
                            'name': 'test-input-bucket'
                        },
                        'object': {
                            'key': 'test-report.pdf'
                        }
                    }
                }
            ]
        }
        
        # Create mock context
        self.context = MagicMock()
    
    @patch('app.s3_service')
    @patch('app.textract_service')
    @patch('app.bedrock_service')
    @patch('app.ses_service')
    def test_lambda_handler_success(self, mock_ses, mock_bedrock, mock_textract, mock_s3):
        """Test successful execution of the Lambda handler."""
        # Configure mocks
        mock_s3.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_s3.generate_presigned_url.return_value = 'https://example.com/test-url'
        mock_textract.extract_text.return_value = 'Extracted text from PDF'
        mock_bedrock.analyze_soc2_report.return_value = {
            'Report Overview': {
                'Service Organization name': 'Test Org',
                'Service Auditor name': 'Test Auditor',
                'Report Type': 'Type 2',
                'Report Period': '2023-01-01 to 2023-12-31'
            }
        }
        
        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertIn('SOC2 report analysis completed successfully', response_body['message'])
        
        # Verify the mocks were called correctly
        mock_s3.get_object.assert_called_once_with('test-input-bucket', 'test-report.pdf')
        mock_textract.extract_text.assert_called_once()
        mock_bedrock.analyze_soc2_report.assert_called_once_with('Extracted text from PDF')
        mock_s3.put_object.assert_called_once()
        mock_ses.send_notification.assert_called_once()
    
    @patch('app.validate_event')
    def test_lambda_handler_invalid_event(self, mock_validate_event):
        """Test handling of invalid events."""
        # Configure mock to raise ValidationError
        mock_validate_event.side_effect = ValidationError("Invalid event structure")
        
        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('ValidationError', response_body['type'])
    
    @patch('app.validate_event')
    @patch('app.s3_service')
    @patch('utils.validation.validate_pdf_file')
    def test_lambda_handler_invalid_pdf(self, mock_validate_pdf, mock_s3, mock_validate_event):
        """Test handling of invalid PDF files."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.get_object.return_value = b'Not a PDF file'
        
        # Make validate_pdf_file raise a ValidationError
        mock_validate_pdf.side_effect = ValidationError("Invalid file format: Not a PDF file")
        
        # We need to patch app.s3_service.get_object to raise the ValidationError
        # when the PDF content is validated
        with patch('app.s3_service.get_object') as mock_get_object:
            mock_get_object.side_effect = ValidationError("Invalid file format: Not a PDF file")
            
            # Call the Lambda handler
            response = lambda_handler(self.event, self.context)
            
            # Verify the response
            self.assertEqual(response['statusCode'], 400)
            self.assertIn('ValidationError', response['body'])
    
    @patch('app.validate_event')
    @patch('app.s3_service')
    @patch('app.textract_service')
    def test_lambda_handler_textract_error(self, mock_textract, mock_s3, mock_validate_event):
        """Test handling of Textract errors."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_textract.extract_text.side_effect = Exception("Textract service error")
        
        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('InternalServerError', response_body['type'])
    
    @patch('app.validate_event')
    @patch('app.s3_service')
    @patch('app.textract_service')
    @patch('app.bedrock_service')
    def test_lambda_handler_bedrock_error(self, mock_bedrock, mock_textract, mock_s3, mock_validate_event):
        """Test handling of Bedrock errors."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_textract.extract_text.return_value = 'Extracted text from PDF'
        mock_bedrock.analyze_soc2_report.side_effect = Exception("Bedrock service error")
        
        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('InternalServerError', response_body['type'])

if __name__ == '__main__':
    unittest.main() 