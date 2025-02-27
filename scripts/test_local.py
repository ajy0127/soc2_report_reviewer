#!/usr/bin/env python3
"""
Local testing script for SOC2-Analyzer

This script allows you to test the SOC2-Analyzer functionality locally
using sample SOC2 reports from the Example_SOC2Reports folder.
"""

import os
import sys
import json
import logging
import io
from pathlib import Path
import PyPDF2

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Import the services
from services.s3_service import S3Service
from services.textract_service import TextractService
from services.bedrock_service import BedrockService
from services.ses_service import SESService
from utils.validation import validate_pdf_file

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('soc2-analyzer-local')

# Set environment variables for local testing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'  # Change as needed
os.environ['INPUT_BUCKET'] = 'local-test-bucket'
os.environ['OUTPUT_BUCKET'] = 'local-test-bucket'
os.environ['NOTIFICATION_EMAIL'] = 'test@example.com'
os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-v2'  # Change as needed
os.environ['ENVIRONMENT'] = 'local'

class LocalS3Service:
    """Local implementation of S3Service for testing without AWS."""
    
    def get_object(self, bucket, key):
        """Read a file from the local filesystem instead of S3."""
        file_path = Path(key)
        with open(file_path, 'rb') as f:
            return f.read()
    
    def put_object(self, bucket, key, body):
        """Write a file to the local filesystem instead of S3."""
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(key), exist_ok=True)
        
        with open(key, 'w') as f:
            f.write(body)
        logger.info(f"Saved result to {key}")
        return True
    
    def generate_presigned_url(self, bucket, key):
        """Generate a fake presigned URL for local testing."""
        return f"file://{os.path.abspath(key)}"

class LocalTextractService:
    """Local implementation of TextractService for testing without AWS."""
    
    def extract_text(self, pdf_content):
        """
        Extract text from a PDF using PyPDF2 instead of Textract.
        
        Args:
            pdf_content (bytes): The PDF content as bytes
            
        Returns:
            str: The extracted text
        """
        logger.info("Extracting text from PDF using PyPDF2")
        
        try:
            # Create a PDF file reader object
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from each page
            text = ""
            num_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            # Only process the first 10 pages for speed in local testing
            max_pages = min(10, num_pages)
            
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                
                # Log progress for large documents
                if page_num % 5 == 0 and page_num > 0:
                    logger.info(f"Processed {page_num} of {max_pages} pages")
            
            logger.info(f"Successfully extracted {len(text)} characters of text")
            
            # If we limited the pages, add a note
            if max_pages < num_pages:
                text += f"\n\n[Note: Only the first {max_pages} pages of {num_pages} were processed for local testing]"
                
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return f"Error extracting text: {str(e)}"

class LocalBedrockService:
    """Local implementation of BedrockService for testing without AWS."""
    
    def analyze_soc2_report(self, text):
        """
        For local testing, we'll return a mock analysis result.
        
        In a real implementation with Bedrock, this would send the text to an LLM
        for analysis and return the structured results.
        """
        logger.info("Analyzing SOC2 report (local mock)")
        
        # Extract a small sample of the text to include in the mock result
        text_sample = text[:500] + "..." if len(text) > 500 else text
        
        return {
            "Report Overview": {
                "Service Organization name": "Example Organization",
                "Report Type": "SOC 2 Type 2",
                "Period Covered": "January 1, 2023 to December 31, 2023"
            },
            "Controls Summary": {
                "Total Controls": 100,
                "Passing Controls": 95,
                "Failing Controls": 5
            },
            "Key Findings": [
                "The organization has implemented strong access controls",
                "Regular security assessments are performed",
                "Some improvements needed in change management processes"
            ],
            "Recommendations": [
                "Strengthen change management documentation",
                "Enhance monitoring of third-party access",
                "Implement additional encryption for data in transit"
            ],
            "Text Sample": text_sample
        }

class LocalSESService:
    """Local implementation of SESService for testing without AWS."""
    
    def send_notification(self, recipient, subject, analysis_result, result_url):
        """
        For local testing, we'll just log the email details.
        """
        logger.info(f"Would send email to: {recipient}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Result URL: {result_url}")
        logger.info("Analysis Summary:")
        logger.info(json.dumps(analysis_result, indent=2))
        return {"MessageId": "local-test-message-id"}

def process_soc2_report(file_path):
    """
    Process a SOC2 report using the same logic as the Lambda function.
    
    Args:
        file_path (str): Path to the SOC2 report PDF file
    """
    logger.info(f"Processing SOC2 report: {file_path}")
    
    try:
        # Initialize local service implementations
        s3_service = LocalS3Service()
        textract_service = LocalTextractService()
        bedrock_service = LocalBedrockService()
        ses_service = LocalSESService()
        
        # Read the PDF file
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Validate the PDF file
        validate_pdf_file(pdf_content)
        logger.info("PDF validation successful")
        
        # Extract text from the PDF
        extracted_text = textract_service.extract_text(pdf_content)
        logger.info(f"Successfully extracted text from {file_path}")
        
        # Analyze the text
        analysis_result = bedrock_service.analyze_soc2_report(extracted_text)
        logger.info("Successfully analyzed SOC2 report")
        
        # Save the analysis result
        output_key = f"results/{os.path.basename(file_path).replace('.pdf', '')}_analysis.json"
        s3_service.put_object('local-test-bucket', output_key, json.dumps(analysis_result, indent=2))
        
        # Send notification
        result_url = s3_service.generate_presigned_url('local-test-bucket', output_key)
        ses_service.send_notification(
            os.environ.get('NOTIFICATION_EMAIL'),
            f"SOC2 Analysis Complete: {os.path.basename(file_path)}",
            analysis_result,
            result_url
        )
        
        logger.info(f"Processing complete for {file_path}")
        logger.info(f"Results saved to {output_key}")
        
    except Exception as e:
        logger.error(f"Error processing SOC2 report: {str(e)}", exc_info=True)

def main():
    """Main function to process all SOC2 reports in the example folder."""
    example_dir = Path("Example_SOC2Reports")
    results_dir = Path("results")
    
    # Create results directory if it doesn't exist
    results_dir.mkdir(exist_ok=True)
    
    # Process each PDF file in the example directory
    pdf_files = list(example_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {example_dir}")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    for pdf_file in pdf_files:
        process_soc2_report(pdf_file)
    
    logger.info("All SOC2 reports processed successfully")
    logger.info(f"Results are available in the {results_dir} directory")

if __name__ == "__main__":
    main() 