"""
Tests for the SES service module.
"""

import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

# Import the module to test
from lambda_package.services.ses_service import (
    send_email,
    send_notification,  # This is the alias for send_email
    create_email_body_html,
    create_email_body_text
)

# Test data
TEST_RECIPIENT = "test@example.com"
TEST_REPORT_NAME = "reports/test_report.pdf"
TEST_ANALYSIS_RESULT = {
    "executive_summary": "This is a test summary",
    "quality_rating": 4,
    "controls": [
        {
            "id": "C1",
            "description": "Test control",
            "effectiveness": "Effective"
        }
    ],
    "framework_mappings": {
        "NIST": ["AC-1", "AC-2"]
    },
    "identified_gaps": ["Gap 1", "Gap 2"]
}


class TestSESService:
    """Tests for the SES service module."""

    def test_create_email_body_text(self):
        """Test creating a plain text email body."""
        # Execute
        body = create_email_body_text(TEST_REPORT_NAME, TEST_ANALYSIS_RESULT)
        
        # Verify
        assert TEST_REPORT_NAME in body
        assert "This is a test summary" in body
        assert "4/5" in body
        assert "C1" in body
        assert "Test control" in body
        assert "Gap 1" in body
        assert "Gap 2" in body

    def test_create_email_body_html(self):
        """Test creating an HTML email body."""
        # Execute
        body = create_email_body_html(TEST_REPORT_NAME, TEST_ANALYSIS_RESULT)
        
        # Verify
        assert TEST_REPORT_NAME in body
        assert "This is a test summary" in body
        assert "4/5" in body
        assert "C1" in body
        assert "Test control" in body
        assert "Gap 1" in body
        assert "Gap 2" in body
        assert "<html" in body
        assert "</html>" in body

    @patch("lambda_package.services.ses_service.boto3")
    def test_send_email_success(self, mock_boto3):
        """Test sending an email successfully."""
        # Setup
        mock_ses = MagicMock()
        mock_boto3.client.return_value = mock_ses
        mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
        
        # Execute
        result = send_email(TEST_RECIPIENT, TEST_REPORT_NAME, TEST_ANALYSIS_RESULT)
        
        # Verify
        assert result is True
        mock_boto3.client.assert_called_once_with("ses")
        mock_ses.send_email.assert_called_once()
        call_args = mock_ses.send_email.call_args[1]
        assert call_args["Source"] is not None
        assert call_args["Destination"]["ToAddresses"] == [TEST_RECIPIENT]
        assert "SOC 2 Report Analysis" in call_args["Message"]["Subject"]["Data"]

    @patch("lambda_package.services.ses_service.boto3")
    def test_send_email_error(self, mock_boto3):
        """Test handling errors when sending an email."""
        # Setup
        mock_ses = MagicMock()
        mock_boto3.client.return_value = mock_ses
        mock_ses.send_email.side_effect = ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "Email address is not verified."}},
            "SendEmail"
        )
        
        # Execute and verify
        with pytest.raises(Exception) as excinfo:
            send_email(TEST_RECIPIENT, TEST_REPORT_NAME, TEST_ANALYSIS_RESULT)
        
        assert "Error sending email" in str(excinfo.value)

    @patch("lambda_package.services.ses_service.boto3")
    def test_send_notification_alias(self, mock_boto3):
        """Test that send_notification is an alias for send_email."""
        # Setup
        mock_ses = MagicMock()
        mock_boto3.client.return_value = mock_ses
        mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
        
        # Execute
        result = send_notification(TEST_RECIPIENT, TEST_REPORT_NAME, TEST_ANALYSIS_RESULT)
        
        # Verify
        assert result is True
        mock_boto3.client.assert_called_once_with("ses")
        mock_ses.send_email.assert_called_once() 