"""
Tests for the Bedrock service.
"""
import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Add the lambda_code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_code'))

# Import the Bedrock service
from bedrock_service import analyze_text, create_prompt, extract_json_from_response

class TestBedrockService:
    """Test cases for the Bedrock service."""

    @patch('bedrock_service.boto3.client')
    @patch('bedrock_service.validate_analysis_result')
    def test_analyze_text_success(self, mock_validate, mock_boto3_client, sample_bedrock_response, mock_env_vars):
        """Test the analyze_text function with a successful response."""
        # Mock the Bedrock client
        mock_bedrock = MagicMock()
        mock_boto3_client.return_value = mock_bedrock
        
        # Mock the invoke_model method
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(
                read=MagicMock(return_value=json.dumps({
                    'content': [{'text': sample_bedrock_response['completion']}]
                }).encode('utf-8'))
            )
        }
        
        # Mock the validate_analysis_result function
        mock_validate.return_value = True
        
        # Call the analyze_text function
        result = analyze_text("This is a sample SOC 2 report text for analysis.")
        
        # Verify the result
        assert "executive_summary" in result
        assert "quality_rating" in result
        assert "controls" in result
        assert "framework_mappings" in result
        assert "identified_gaps" in result
        
        # Verify that the Bedrock client was called with the correct arguments
        mock_bedrock.invoke_model.assert_called_once()
        
        # Verify that the validation function was called
        mock_validate.assert_called_once()

    @patch('bedrock_service.boto3.client')
    def test_analyze_text_client_error(self, mock_boto3_client, mock_env_vars):
        """Test the analyze_text function with a ClientError."""
        # Mock the Bedrock client
        mock_bedrock = MagicMock()
        mock_boto3_client.return_value = mock_bedrock
        
        # Mock the invoke_model method to raise a ClientError
        error_response = {
            'Error': {
                'Code': 'ModelNotReadyException',
                'Message': 'The model is not ready for invocation'
            }
        }
        mock_bedrock.invoke_model.side_effect = ClientError(
            error_response, 'InvokeModel')
        
        # Call the analyze_text function and expect an exception
        from utils.error_handling import BedrockError
        with pytest.raises(BedrockError) as excinfo:
            analyze_text("This is a sample SOC 2 report text for analysis.")
        
        # Verify the exception message
        assert "The model is not ready for invocation" in str(excinfo.value)

    @patch('bedrock_service.boto3.client')
    @patch('bedrock_service.validate_analysis_result')
    def test_analyze_text_validation_error(self, mock_validate, mock_boto3_client, sample_bedrock_response, mock_env_vars):
        """Test the analyze_text function with a validation error."""
        # Mock the Bedrock client
        mock_bedrock = MagicMock()
        mock_boto3_client.return_value = mock_bedrock
        
        # Mock the invoke_model method
        mock_bedrock.invoke_model.return_value = {
            'body': MagicMock(
                read=MagicMock(return_value=json.dumps({
                    'content': [{'text': sample_bedrock_response['completion']}]
                }).encode('utf-8'))
            )
        }
        
        # Mock the validate_analysis_result function to raise an exception
        from utils.error_handling import ValidationError
        mock_validate.side_effect = ValidationError("Invalid analysis result")
        
        # Call the analyze_text function and expect an exception
        with pytest.raises(ValidationError) as excinfo:
            analyze_text("This is a sample SOC 2 report text for analysis.")
        
        # Verify the exception message
        assert "Invalid analysis result" in str(excinfo.value)

    def test_create_prompt(self):
        """Test the create_prompt function."""
        # Call the create_prompt function
        prompt = create_prompt("This is a sample SOC 2 report text for analysis.")
        
        # Verify the prompt contains the expected elements
        assert "SOC 2 report" in prompt
        assert "scope" in prompt
        assert "controls" in prompt
        assert "cis_mapping" in prompt
        assert "owasp_mapping" in prompt
        assert "gaps" in prompt
        assert "summary" in prompt
        assert "quality_rating" in prompt
        assert "This is a sample SOC 2 report text for analysis." in prompt

    def test_extract_json_from_response_valid(self):
        """Test the extract_json_from_response function with valid JSON."""
        # Valid JSON response
        response_text = """
        Here's the analysis of the SOC 2 report:
        
        ```json
        {
            "executive_summary": "This is a test summary.",
            "quality_rating": 4.5,
            "controls": [],
            "framework_mappings": {},
            "identified_gaps": []
        }
        ```
        """
        
        # Call the extract_json_from_response function
        result = extract_json_from_response(response_text)
        
        # Verify the result
        assert result["executive_summary"] == "This is a test summary."
        assert result["quality_rating"] == 4.5
        assert isinstance(result["controls"], list)
        assert isinstance(result["framework_mappings"], dict)
        assert isinstance(result["identified_gaps"], list)

    def test_extract_json_from_response_invalid(self):
        """Test the extract_json_from_response function with invalid JSON."""
        # Invalid JSON response
        response_text = """
        Here's the analysis of the SOC 2 report:
        
        ```json
        {
            "executive_summary": "This is a test summary.",
            "quality_rating": 4.5,
            "controls": [],
            "framework_mappings": {},
            "identified_gaps": []
        ```
        """
        
        # Call the extract_json_from_response function and expect an exception
        from utils.error_handling import BedrockError
        with pytest.raises(BedrockError) as excinfo:
            extract_json_from_response(response_text)
        
        # Verify the exception message
        assert "Could not extract valid JSON from model response" in str(excinfo.value)

    def test_extract_json_from_response_no_json(self):
        """Test the extract_json_from_response function with no JSON."""
        # Response with no JSON
        response_text = "Here's the analysis of the SOC 2 report without any JSON."
        
        # Call the extract_json_from_response function and expect an exception
        from utils.error_handling import BedrockError
        with pytest.raises(BedrockError) as excinfo:
            extract_json_from_response(response_text)
        
        # Verify the exception message
        assert "Could not extract valid JSON from model response" in str(excinfo.value) 