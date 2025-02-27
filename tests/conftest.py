import os
import sys
import pytest

# Set AWS region before importing boto3
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Set environment variables for testing
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up environment variables for testing."""
    # Save original environment variables
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['INPUT_BUCKET'] = 'test-input-bucket'
    os.environ['OUTPUT_BUCKET'] = 'test-output-bucket'
    os.environ['NOTIFICATION_EMAIL'] = 'test@example.com'
    os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)

# Mock AWS services
@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for boto3."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def s3_event():
    """Create a mock S3 event."""
    return {
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

@pytest.fixture
def direct_event():
    """Create a mock direct invocation event."""
    return {
        'bucket': 'test-input-bucket',
        'key': 'test-report.pdf'
    }

@pytest.fixture
def eventbridge_event():
    """Create a mock EventBridge event."""
    return {
        'detail': {
            'bucket': {
                'name': 'test-input-bucket'
            },
            'object': {
                'key': 'test-report.pdf'
            }
        }
    }

@pytest.fixture
def mock_pdf_content():
    """Create mock PDF content."""
    return b'%PDF-1.7\nTest PDF content\n%%EOF' 