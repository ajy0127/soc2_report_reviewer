import unittest
import json
import os
import sys
from unittest.mock import patch

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

    @patch('lambda.app.validate_event')
    @patch('lambda.app.S3Service')
    @patch('lambda.app.OCRmyPDFService')
    @patch('lambda.app.BedrockService')
    @patch('lambda.app.SESService')
    def test_lambda_handler_success(self, mock_ses, mock_bedrock, mock_ocrmypdf, mock_s3, mock_validate):
        """Test successful execution of the Lambda handler."""
        # Configure mocks
        mock_validate.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.return_value.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_ocrmypdf.return_value.extract_text.return_value = 'Extracted text from PDF'
        mock_bedrock.return_value.analyze_soc2_report.return_value = {
            'Report Overview': {
                'Service Organization name': 'Test Org',
                'Service Auditor name': 'Test Auditor',
                'Report Type': 'Type 2',
                'Report Period': '2023-01-01 to 2023-12-31'
            }
        }
        mock_s3.return_value.put_object.return_value = 'test-output-key.json'
        mock_s3.return_value.generate_presigned_url.return_value = 'https://example.com/test-url'
        mock_ses.return_value.send_notification.return_value = {'MessageId': 'test-message-id'}

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
        mock_validate.assert_called_once_with(self.event)
        mock_s3.return_value.get_object.assert_called_once_with('test-input-bucket', 'test-report.pdf')
        mock_s3.return_value.put_object.assert_called_once()
        mock_s3.return_value.generate_presigned_url.assert_called_once()
        mock_ses.return_value.send_notification.assert_called_once()

    @patch('lambda.app.validate_event')
    def test_lambda_handler_invalid_event(self, mock_validate):
        """Test handling of invalid events."""
        # Configure mock to raise ValidationError
        mock_validate.side_effect = ValidationError("Invalid event structure")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('Invalid event structure', response_body['error'])

    @patch('lambda.app.validate_event')
    @patch('lambda.app.S3Service')
    def test_lambda_handler_s3_error(self, mock_s3, mock_validate):
        """Test handling of S3 service errors."""
        # Configure mocks
        mock_validate.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.return_value.get_object.side_effect = Exception("S3 service error")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('S3 service error', response_body['error'])

    @patch('lambda.app.validate_event')
    @patch('lambda.app.S3Service')
    @patch('lambda.app.OCRmyPDFService')
    def test_lambda_handler_textract_error(self, mock_ocrmypdf, mock_s3, mock_validate):
        """Test handling of OCRmyPDF service errors."""
        # Configure mocks
        mock_validate.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.return_value.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_ocrmypdf.return_value.extract_text.side_effect = Exception("OCR processing failed")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('OCR processing failed', response_body['error'])

    @patch('lambda.app.validate_event')
    @patch('lambda.app.S3Service')
    @patch('lambda.app.OCRmyPDFService')
    @patch('lambda.app.BedrockService')
    def test_lambda_handler_bedrock_error(self, mock_bedrock, mock_ocrmypdf, mock_s3, mock_validate):
        """Test handling of Bedrock service errors."""
        # Configure mocks
        mock_validate.return_value = ('test-input-bucket', 'test-report.pdf')
        mock_s3.return_value.get_object.return_value = b'%PDF-1.7\nTest PDF content\n%%EOF'
        mock_ocrmypdf.return_value.extract_text.return_value = 'Extracted text from PDF'
        mock_bedrock.return_value.analyze_soc2_report.side_effect = Exception("Bedrock processing failed")

        # Call the Lambda handler
        response = lambda_handler(self.event, self.context)

        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertIn('Bedrock processing failed', response_body['error'])

if __name__ == '__main__':
    unittest.main() 