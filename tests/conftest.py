"""
Pytest configuration file for SOC 2 Report Analysis Tool tests.
"""
import os
import sys
import pytest

# Add the lambda_code directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lambda_code')))

# Define fixtures that can be reused across tests
@pytest.fixture
def sample_s3_event():
    """
    Returns a sample S3 event that would trigger the Lambda function.
    """
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2023-01-01T12:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "EXAMPLE"
                },
                "requestParameters": {
                    "sourceIPAddress": "127.0.0.1"
                },
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": "soc2-reports-bucket",
                        "ownerIdentity": {
                            "principalId": "EXAMPLE"
                        },
                        "arn": "arn:aws:s3:::soc2-reports-bucket"
                    },
                    "object": {
                        "key": "reports/sample-soc2-report.pdf",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901"
                    }
                }
            }
        ]
    }

@pytest.fixture
def sample_textract_response():
    """
    Returns a sample response from the Textract service.
    """
    return {
        "Blocks": [
            {
                "BlockType": "LINE",
                "Text": "SOC 2 Type 2 Report",
                "Confidence": 99.8
            },
            {
                "BlockType": "LINE",
                "Text": "Control Environment",
                "Confidence": 99.5
            },
            {
                "BlockType": "LINE",
                "Text": "The organization maintains a strong control environment.",
                "Confidence": 98.7
            }
        ],
        "DocumentMetadata": {
            "Pages": 1
        }
    }

@pytest.fixture
def sample_bedrock_response():
    """
    Returns a sample response from the Bedrock service.
    """
    return {
        "completion": """
        {
            "executive_summary": "This is a high-quality SOC 2 Type 2 report that demonstrates a strong control environment.",
            "quality_rating": 4.5,
            "controls": [
                {
                    "id": "CC1.1",
                    "description": "The entity demonstrates a commitment to integrity and ethical values.",
                    "effectiveness": "Effective"
                },
                {
                    "id": "CC2.1",
                    "description": "The entity's board of directors demonstrates independence from management.",
                    "effectiveness": "Effective"
                }
            ],
            "framework_mappings": {
                "CIS": ["1.1", "2.3"],
                "OWASP": ["A1", "A3"]
            },
            "identified_gaps": [
                "No significant gaps identified."
            ]
        }
        """
    }

@pytest.fixture
def mock_env_vars():
    """
    Sets up mock environment variables for testing.
    """
    original_env = os.environ.copy()
    os.environ["STAKEHOLDER_EMAIL"] = "test@example.com"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env) 