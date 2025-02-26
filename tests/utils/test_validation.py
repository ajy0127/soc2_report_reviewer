"""
Tests for the validation utilities.
"""

import pytest
import json
import sys
import os

# Add the lambda_code directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_code'))

from utils.validation import (
    validate_pdf_file,
    validate_s3_event,
    validate_analysis_result,
    is_valid_pdf,
    validate_json_format
)
from utils.error_handling import ValidationError

class TestValidation:
    """Test cases for validation utilities."""

    def test_is_valid_pdf(self):
        """Test the is_valid_pdf function."""
        assert is_valid_pdf("test.pdf") is True
        assert is_valid_pdf("test.PDF") is True
        assert is_valid_pdf("test.txt") is False
        assert is_valid_pdf("test") is False

    def test_validate_json_format(self):
        """Test the validate_json_format function."""
        assert validate_json_format('{"key": "value"}') is True
        assert validate_json_format('{"key": 123}') is True
        assert validate_json_format('{"key": [1, 2, 3]}') is True
        assert validate_json_format('{"key": {"nested": "value"}}') is True
        assert validate_json_format('not json') is False
        assert validate_json_format('{"key": value}') is False
        assert validate_json_format('{"key": "value"') is False

    def test_validate_s3_event_valid(self, sample_s3_event):
        """Test that a valid S3 event passes validation."""
        # This should not raise an exception
        bucket, key = validate_s3_event(sample_s3_event)
        assert bucket == "soc2-reports-bucket"
        assert key == "reports/sample-soc2-report.pdf"

    def test_validate_s3_event_invalid_no_records(self):
        """Test that an S3 event with no records fails validation."""
        invalid_event = {"Records": []}
        with pytest.raises(ValidationError):
            validate_s3_event(invalid_event)

    def test_validate_s3_event_invalid_no_s3(self):
        """Test that an S3 event with no s3 data fails validation."""
        invalid_event = {
            "Records": [
                {
                    "eventSource": "aws:s3",
                    "eventName": "ObjectCreated:Put"
                    # Missing s3 data
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate_s3_event(invalid_event)

    def test_validate_pdf_file_valid(self, mocker):
        """Test that a valid PDF file passes validation."""
        # Mock the S3 client and response
        mock_s3_client = mocker.Mock()
        mock_s3_client.head_object.return_value = {
            "ContentType": "application/pdf",
            "ContentLength": 1024
        }
        
        # This should not raise an exception
        validate_pdf_file(mock_s3_client, "test-bucket", "test-key.pdf")
        
        # Verify the S3 client was called correctly
        mock_s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key.pdf"
        )

    def test_validate_pdf_file_invalid_content_type(self, mocker):
        """Test that a non-PDF file fails validation."""
        # Mock the S3 client and response
        mock_s3_client = mocker.Mock()
        mock_s3_client.head_object.return_value = {
            "ContentType": "text/plain",
            "ContentLength": 1024
        }
        
        with pytest.raises(ValidationError):
            validate_pdf_file(mock_s3_client, "test-bucket", "test-key.txt")

    def test_validate_pdf_file_too_large(self, mocker):
        """Test that a PDF file that's too large fails validation."""
        # Mock the S3 client and response
        mock_s3_client = mocker.Mock()
        mock_s3_client.head_object.return_value = {
            "ContentType": "application/pdf",
            "ContentLength": 100 * 1024 * 1024  # 100 MB
        }
        
        with pytest.raises(ValidationError):
            validate_pdf_file(mock_s3_client, "test-bucket", "test-key.pdf")

    def test_validate_analysis_result_valid(self, sample_bedrock_response):
        """Test that a valid analysis result passes validation."""
        # Parse the JSON from the sample response
        result = json.loads(sample_bedrock_response["completion"].strip())
        
        # This should not raise an exception
        validate_analysis_result(result)

    def test_validate_analysis_result_missing_fields(self):
        """Test that an analysis result with missing fields fails validation."""
        invalid_result = {
            "executive_summary": "This is a test summary.",
            # Missing other required fields
        }
        
        with pytest.raises(ValidationError):
            validate_analysis_result(invalid_result)

    def test_validate_analysis_result_invalid_quality_rating(self):
        """Test that an analysis result with an invalid quality rating fails validation."""
        invalid_result = {
            "executive_summary": "This is a test summary.",
            "quality_rating": 6.0,  # Should be between 0 and 5
            "controls": [],
            "framework_mappings": {},
            "identified_gaps": []
        }
        
        with pytest.raises(ValidationError):
            validate_analysis_result(invalid_result) 