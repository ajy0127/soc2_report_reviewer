"""
Tests for the S3 service module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Import the module to test
from lambda_package.services.s3_service import (
    store_analysis,
    tag_pdf,
    get_s3_object,
    S3Error
)

# Test data
TEST_BUCKET = "test-bucket"
TEST_KEY = "test/key.pdf"
TEST_ANALYSIS_KEY = "test/key_analysis.json"
TEST_ANALYSIS = {"key": "value", "findings": ["test finding"]}
TEST_TAG_KEY = "Status"
TEST_TAG_VALUE = "Analyzed"


class TestS3Service:
    """Tests for the S3 service module."""

    @patch("lambda_package.services.s3_service.boto3")
    def test_store_analysis_success(self, mock_boto3):
        """Test storing analysis result successfully."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        
        # Execute
        store_analysis(TEST_BUCKET, TEST_ANALYSIS_KEY, TEST_ANALYSIS)
        
        # Verify
        mock_boto3.client.assert_called_once_with("s3")
        mock_s3.put_object.assert_called_once()
        call_args = mock_s3.put_object.call_args[1]
        assert call_args["Bucket"] == TEST_BUCKET
        assert call_args["Key"] == TEST_ANALYSIS_KEY
        assert call_args["ContentType"] == "application/json"
        # Verify JSON was properly formatted
        stored_json = json.loads(call_args["Body"])
        assert stored_json == TEST_ANALYSIS

    @patch("lambda_package.services.s3_service.boto3")
    def test_store_analysis_error(self, mock_boto3):
        """Test handling errors when storing analysis."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "PutObject"
        )
        
        # Execute and verify
        with pytest.raises(S3Error) as excinfo:
            store_analysis(TEST_BUCKET, TEST_ANALYSIS_KEY, TEST_ANALYSIS)
        
        assert "Error storing analysis in S3" in str(excinfo.value)

    @patch("lambda_package.services.s3_service.boto3")
    def test_tag_pdf_success_new_tag(self, mock_boto3):
        """Test tagging a PDF with a new tag."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.get_object_tagging.return_value = {"TagSet": []}
        
        # Execute
        tag_pdf(TEST_BUCKET, TEST_KEY, TEST_TAG_KEY, TEST_TAG_VALUE)
        
        # Verify
        mock_boto3.client.assert_called_with("s3")
        mock_s3.put_object_tagging.assert_called_once()
        call_args = mock_s3.put_object_tagging.call_args[1]
        assert call_args["Bucket"] == TEST_BUCKET
        assert call_args["Key"] == TEST_KEY
        assert call_args["Tagging"]["TagSet"] == [{"Key": TEST_TAG_KEY, "Value": TEST_TAG_VALUE}]

    @patch("lambda_package.services.s3_service.boto3")
    def test_tag_pdf_success_update_tag(self, mock_boto3):
        """Test updating an existing tag on a PDF."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.get_object_tagging.return_value = {
            "TagSet": [{"Key": TEST_TAG_KEY, "Value": "OldValue"}]
        }
        
        # Execute
        tag_pdf(TEST_BUCKET, TEST_KEY, TEST_TAG_KEY, TEST_TAG_VALUE)
        
        # Verify
        mock_boto3.client.assert_called_with("s3")
        mock_s3.put_object_tagging.assert_called_once()
        call_args = mock_s3.put_object_tagging.call_args[1]
        assert call_args["Bucket"] == TEST_BUCKET
        assert call_args["Key"] == TEST_KEY
        assert call_args["Tagging"]["TagSet"] == [{"Key": TEST_TAG_KEY, "Value": TEST_TAG_VALUE}]

    @patch("lambda_package.services.s3_service.boto3")
    def test_get_s3_object_success(self, mock_boto3):
        """Test retrieving an S3 object successfully."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_response = {
            "Body": MagicMock(),
            "ContentLength": 1024,
            "ContentType": "application/pdf"
        }
        mock_s3.get_object.return_value = mock_response
        
        # Execute
        response = get_s3_object(TEST_BUCKET, TEST_KEY)
        
        # Verify
        assert response == mock_response
        mock_boto3.client.assert_called_once()
        mock_s3.get_object.assert_called_once_with(Bucket=TEST_BUCKET, Key=TEST_KEY)

    @patch("lambda_package.services.s3_service.boto3")
    def test_get_s3_object_with_url_encoded_key(self, mock_boto3):
        """Test retrieving an S3 object with a URL-encoded key."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_response = {
            "Body": MagicMock(),
            "ContentLength": 1024,
            "ContentType": "application/pdf"
        }
        mock_s3.get_object.return_value = mock_response
        encoded_key = "test/file+with+spaces.pdf"
        decoded_key = "test/file with spaces.pdf"
        
        # Execute
        response = get_s3_object(TEST_BUCKET, encoded_key)
        
        # Verify
        assert response == mock_response
        mock_boto3.client.assert_called_once()
        mock_s3.get_object.assert_called_once_with(Bucket=TEST_BUCKET, Key=decoded_key)

    @patch("lambda_package.services.s3_service.boto3")
    def test_get_s3_object_error(self, mock_boto3):
        """Test handling errors when retrieving an S3 object."""
        # Setup
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "GetObject"
        )
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject"
        )
        mock_s3.list_objects_v2.return_value = {"KeyCount": 0}
        
        # Execute and verify
        with pytest.raises(S3Error) as excinfo:
            get_s3_object(TEST_BUCKET, TEST_KEY)
        
        assert "Error accessing S3 object" in str(excinfo.value) 