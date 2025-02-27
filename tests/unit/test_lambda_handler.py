import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the path and import the lambda handler
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
# Import using __import__ to avoid the keyword issue
app_module = __import__('lambda.app', fromlist=['lambda_handler'])
lambda_handler = app_module.lambda_handler
from utils.validation import ValidationError

class TestLambdaHandler(unittest.TestCase):
    """Test cases for the Lambda handler function."""

    def setUp(self):
        """Set up test fixtures."""
        # Set environment variables for testing
        os.environ['INPUT_BUCKET'] = 'test-input-bucket'
        os.environ['OUTPUT_BUCKET'] = 'test-output-bucket'
        os.environ['NOTIFICATION_EMAIL'] = 'test@example.com'
        os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-v2'
        os.environ['ENVIRONMENT'] = 'test'

        # Sample S3 event
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
        self.context = {}

    @patch('boto3.client')
    @patch('lambda.app.validate_event')
    @patch('services.s3_service.S3Service.get_object')
    @patch('lambda.app.validate_pdf_file')
    @patch('services.ocrmypdf_service.OCRmyPDFService.extract_text')
    @patch('services.bedrock_service.BedrockService.analyze_soc2_report')
    @patch('services.s3_service.S3Service.put_object')
    @patch('services.s3_service.S3Service.generate_presigned_url')
    @patch('services.ses_service.SESService.send_notification')
    def test_lambda_handler_success(self, mock_send_notification, mock_generate_url, 
                                   mock_put_object, mock_analyze_soc2, mock_extract_text,
                                   mock_validate_pdf, mock_get_object, mock_validate_event, mock_boto3):
        """Test successful execution of the Lambda handler."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_validate_pdf.return_value = True
        mock_extract_text.return_value = 'Extracted text from PDF'
        mock_analyze_soc2.return_value = {
            'Report Overview': {
                'Service Organization name': 'Test Org',
                'Service Auditor name': 'Test Auditor',
                'Report Type': 'Type 2',
                'Report Period': '2023-01-01 to 2023-12-31'
            }
        }
        mock_put_object.return_value = 'test-output-key.json'
        mock_generate_url.return_value = 'https://example.com/test-url'
        mock_send_notification.return_value = {'MessageId': 'test-message-id'}

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertIn('message', response_body)
        self.assertIn('SOC2 report analysis completed successfully', response_body['message'])
        self.assertIn('result_url', response_body)
        self.assertEqual(response_body['result_url'], 'https://example.com/test-url')

        # Verify that all service methods were called
        mock_validate_event.assert_called_once_with(self.event)
        mock_get_object.assert_called_once_with('test-input-bucket', 'test-report.pdf')
        mock_validate_pdf.assert_called_once()
        mock_extract_text.assert_called_once()
        mock_analyze_soc2.assert_called_once()
        mock_put_object.assert_called_once()
        mock_generate_url.assert_called_once()
        mock_send_notification.assert_called_once()

    @patch('boto3.client')
    @patch('lambda.app.validate_event')
    def test_lambda_handler_invalid_event(self, mock_validate_event, mock_boto3):
        """Test handling of invalid events."""
        # Configure mock to raise ValidationError
        mock_validate_event.side_effect = ValidationError("Invalid event structure")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('Invalid event structure', response_body['error'])

    @patch('boto3.client')
    @patch('utils.validation.validate_event')
    @patch('services.s3_service.S3Service.get_object')
    @patch('utils.validation.validate_pdf_file')
    def test_lambda_handler_invalid_pdf(self, mock_validate_pdf, mock_get_object, 
                                       mock_validate_event, mock_boto3):
        """Test handling of invalid PDF files."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_get_object.return_value = b'Not a PDF file'

        # Make validate_pdf_file raise a ValidationError
        mock_validate_pdf.side_effect = ValidationError("Invalid file format: Not a PDF file")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('Invalid file format', response_body['error'])

    @patch('boto3.client')
    @patch('utils.validation.validate_event')
    @patch('services.s3_service.S3Service.get_object')
    @patch('utils.validation.validate_pdf_file')
    @patch('services.ocrmypdf_service.OCRmyPDFService.extract_text')
    def test_lambda_handler_textract_error(self, mock_extract_text, mock_validate_pdf,
                                          mock_get_object, mock_validate_event, mock_boto3):
        """Test handling of OCRmyPDF service errors."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_validate_pdf.return_value = True

        # Make OCRmyPDFService.extract_text raise an exception
        mock_extract_text.side_effect = Exception("OCR processing failed")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('OCR processing failed', response_body['error'])

    @patch('boto3.client')
    @patch('utils.validation.validate_event')
    @patch('services.s3_service.S3Service.get_object')
    @patch('utils.validation.validate_pdf_file')
    @patch('services.ocrmypdf_service.OCRmyPDFService.extract_text')
    @patch('services.bedrock_service.BedrockService.analyze_soc2_report')
    def test_lambda_handler_bedrock_error(self, mock_analyze_soc2, mock_extract_text,
                                         mock_validate_pdf, mock_get_object, 
                                         mock_validate_event, mock_boto3):
        """Test handling of Bedrock service errors."""
        # Configure mocks
        mock_validate_event.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_validate_pdf.return_value = True
        mock_extract_text.return_value = 'Extracted text from PDF'

        # Make BedrockService.analyze_soc2_report raise an exception
        mock_analyze_soc2.side_effect = Exception("Bedrock processing failed")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('Bedrock processing failed', response_body['error'])

if __name__ == '__main__':
    unittest.main() 