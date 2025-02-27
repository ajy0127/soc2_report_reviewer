import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda'))
from utils.validation import validate_event, validate_pdf_file, ValidationError

class TestValidation(unittest.TestCase):
    """Test cases for the validation utility functions."""
    
    def test_validate_event_direct_invocation(self):
        """Test validation of direct invocation events."""
        event = {
            'bucket': 'test-bucket',
            'key': 'test-key.pdf'
        }
        
        bucket_name, object_key = validate_event(event)
        
        self.assertEqual(bucket_name, 'test-bucket')
        self.assertEqual(object_key, 'test-key.pdf')
    
    def test_validate_event_eventbridge(self):
        """Test validation of EventBridge events."""
        event = {
            'detail': {
                'bucket': {
                    'name': 'test-bucket'
                },
                'object': {
                    'key': 'test-key.pdf'
                }
            }
        }
        
        bucket_name, object_key = validate_event(event)
        
        self.assertEqual(bucket_name, 'test-bucket')
        self.assertEqual(object_key, 'test-key.pdf')
    
    def test_validate_event_s3(self):
        """Test validation of S3 events."""
        event = {
            'Records': [
                {
                    'eventSource': 'aws:s3',
                    's3': {
                        'bucket': {
                            'name': 'test-bucket'
                        },
                        'object': {
                            'key': 'test-key.pdf'
                        }
                    }
                }
            ]
        }
        
        bucket_name, object_key = validate_event(event)
        
        self.assertEqual(bucket_name, 'test-bucket')
        self.assertEqual(object_key, 'test-key.pdf')
    
    def test_validate_event_empty(self):
        """Test validation of empty events."""
        with self.assertRaises(ValidationError):
            validate_event(None)
        
        with self.assertRaises(ValidationError):
            validate_event({})
    
    def test_validate_event_invalid_structure(self):
        """Test validation of events with invalid structure."""
        event = {
            'invalid': 'structure'
        }
        
        with self.assertRaises(ValidationError):
            validate_event(event)
    
    def test_validate_pdf_file_valid(self):
        """Test validation of valid PDF files."""
        # Create a mock PDF content
        pdf_content = b'%PDF-1.7\nTest PDF content\n%%EOF'
        
        # Validate the PDF content
        result = validate_pdf_file(pdf_content)
        
        # Verify the result
        self.assertTrue(result)
    
    def test_validate_pdf_file_invalid(self):
        """Test validation of invalid PDF files."""
        # Create an invalid PDF content
        pdf_content = b'Not a PDF file'
        
        # Validate the PDF content
        with self.assertRaises(ValidationError):
            validate_pdf_file(pdf_content)
    
    def test_validate_pdf_file_no_eof(self):
        """Test validation of PDF files without EOF marker."""
        # Create a PDF content without EOF marker
        pdf_content = b'%PDF-1.7\nTest PDF content'
        
        # Validate the PDF content
        result = validate_pdf_file(pdf_content)
        
        # Verify the result (should still pass but log a warning)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main() 