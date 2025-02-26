"""
Tests for the Lambda handler.
"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add the lambda_code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_code'))

# Import the Lambda handler
import app

class TestLambdaHandler:
    """Test cases for the Lambda handler."""

    @patch('app.boto3.client')
    @patch('app.extract_text')
    @patch('app.analyze_text')
    @patch('app.send_email')
    @patch('app.validate_pdf_file')
    @patch('app.validate_s3_event')
    def test_lambda_handler_success(self, mock_validate_s3_event, mock_validate_pdf, mock_send_email, mock_analyze_text, 
                                   mock_extract_text, mock_boto3_client, 
                                   sample_s3_event, sample_textract_response, 
                                   sample_bedrock_response, mock_env_vars):
        """Test the Lambda handler with a successful execution."""
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock the validate_s3_event function
        mock_validate_s3_event.return_value = ("soc2-reports-bucket", "reports/sample-soc2-report.pdf")
        
        # Mock the validate_pdf_file function
        mock_validate_pdf.return_value = True
        
        # Mock the extract_text function
        mock_extract_text.return_value = "Extracted text from the SOC 2 report"
        
        # Mock the analyze_text function
        analysis_result = json.loads(sample_bedrock_response["completion"].strip())
        mock_analyze_text.return_value = analysis_result
        
        # Mock the send_email function
        mock_send_email.return_value = True
        
        # Call the Lambda handler
        response = app.lambda_handler(sample_s3_event, {})
        
        # Verify the response
        assert response["statusCode"] == 200
        assert "Successfully processed" in response["body"]
        
        # Verify that the functions were called with the correct arguments
        mock_extract_text.assert_called_once()
        mock_analyze_text.assert_called_once_with("Extracted text from the SOC 2 report")
        mock_send_email.assert_called_once()
        
        # Verify that the S3 client was used to tag the object
        mock_s3.put_object_tagging.assert_called_once()

    @patch('app.boto3.client')
    def test_lambda_handler_invalid_event(self, mock_boto3_client, sample_s3_event, mock_env_vars):
        """Test the Lambda handler with an invalid S3 event."""
        # Create an invalid event (no Records)
        invalid_event = {"Records": []}
        
        # Call the Lambda handler
        response = app.lambda_handler(invalid_event, {})
        
        # Verify the response
        assert response["statusCode"] == 400
        assert "Invalid S3 event" in response["body"]

    @patch('app.boto3.client')
    @patch('app.validate_pdf_file')
    def test_lambda_handler_invalid_pdf(self, mock_validate_pdf, mock_boto3_client, 
                                       sample_s3_event, mock_env_vars):
        """Test the Lambda handler with an invalid PDF file."""
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock the validate_pdf_file function to raise an exception
        from utils.error_handling import ValidationError
        mock_validate_pdf.side_effect = ValidationError("Invalid PDF file")
        
        # Call the Lambda handler
        response = app.lambda_handler(sample_s3_event, {})
        
        # Verify the response
        assert response["statusCode"] == 400
        assert "Invalid S3 event or PDF file" in response["body"]

    @patch('app.boto3.client')
    @patch('app.validate_pdf_file')
    @patch('app.extract_text')
    @patch('app.validate_s3_event')
    def test_lambda_handler_textract_error(self, mock_validate_s3_event, mock_extract_text, mock_validate_pdf, mock_boto3_client, 
                                          sample_s3_event, mock_env_vars):
        """Test the Lambda handler with a Textract error."""
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock the validate_s3_event function
        mock_validate_s3_event.return_value = ("soc2-reports-bucket", "reports/sample-soc2-report.pdf")
        
        # Mock the validate_pdf_file function
        mock_validate_pdf.return_value = True
        
        # Mock the extract_text function to raise an exception
        from utils.error_handling import TextractError
        mock_extract_text.side_effect = TextractError("Textract error")
        
        # Call the Lambda handler
        response = app.lambda_handler(sample_s3_event, {})
        
        # Verify the response
        assert response["statusCode"] == 500
        assert "Textract error" in response["body"]

    @patch('app.boto3.client')
    @patch('app.validate_pdf_file')
    @patch('app.extract_text')
    @patch('app.analyze_text')
    @patch('app.validate_s3_event')
    def test_lambda_handler_bedrock_error(self, mock_validate_s3_event, mock_analyze_text, mock_extract_text, 
                                         mock_validate_pdf, mock_boto3_client, 
                                         sample_s3_event, mock_env_vars):
        """Test the Lambda handler with a Bedrock error."""
        # Mock the S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        
        # Mock the validate_s3_event function
        mock_validate_s3_event.return_value = ("soc2-reports-bucket", "reports/sample-soc2-report.pdf")
        
        # Mock the validate_pdf_file function
        mock_validate_pdf.return_value = True
        
        # Mock the extract_text function
        mock_extract_text.return_value = "Extracted text from the SOC 2 report"
        
        # Mock the analyze_text function to raise an exception
        from utils.error_handling import BedrockError
        mock_analyze_text.side_effect = BedrockError("Bedrock error")
        
        # Call the Lambda handler
        response = app.lambda_handler(sample_s3_event, {})
        
        # Verify the response
        assert response["statusCode"] == 500
        assert "Bedrock error" in response["body"] 