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
import boto3
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Import the services
from services.s3_service import S3Service
from services.ocrmypdf_service import OCRmyPDFService
from services.bedrock_service import BedrockService
from services.ses_service import SESService
from utils.validation import validate_pdf_file

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('soc2-analyzer-local')

# Set up AWS session with sandbox profile
session = boto3.Session(profile_name='sandbox', region_name='us-east-1')

# Set environment variables for local testing
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['INPUT_BUCKET'] = 'local-test-bucket'
os.environ['OUTPUT_BUCKET'] = 'local-test-bucket'
os.environ['NOTIFICATION_EMAIL'] = 'test@example.com'
os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-v2'
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

def create_test_pdf():
    """Create a test PDF file with sample SOC2 report content."""
    example_dir = Path("Example_SOC2Reports")
    example_dir.mkdir(exist_ok=True)
    
    pdf_path = example_dir / "test_soc2_report.pdf"
    
    # Create PDF with reportlab
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    
    # Add title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Sample SOC2 Type 2 Report")
    
    # Add content
    c.setFont("Helvetica", 12)
    y = 700
    sample_text = [
        "Section I: Independent Service Auditor's Report",
        "",
        "To the Management of Example Organization:",
        "",
        "Scope",
        "We have examined Example Organization's description of its cloud services system...",
        "",
        "Control Objectives and Related Controls",
        "Our examination included procedures to obtain reasonable assurance about whether:",
        "- The description fairly presents the system that was designed and implemented",
        "- The controls stated in the description were suitably designed",
        "- The controls operated effectively throughout the period"
    ]
    
    for line in sample_text:
        c.drawString(72, y, line)
        y -= 20
    
    c.save()
    
    logger.info(f"Created test PDF at {pdf_path}")
    return pdf_path

def process_soc2_report(file_path):
    """
    Process a SOC2 report using the same logic as the Lambda function.
    
    Args:
        file_path (str): Path to the SOC2 report PDF file
    """
    logger.info(f"Processing SOC2 report: {file_path}")
    
    try:
        # Initialize services - using OCRmyPDFService instead of LandingAIService
        s3_service = LocalS3Service()
        ocrmypdf_service = OCRmyPDFService()  # Using OCRmyPDF for text extraction
        bedrock_service = LocalBedrockService()
        ses_service = LocalSESService()
        
        # Read the PDF file
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
        
        # Validate the PDF file
        validate_pdf_file(pdf_content)
        logger.info("PDF validation successful")
        
        # Extract text from the PDF using OCRmyPDF
        extracted_text = ocrmypdf_service.extract_text(pdf_content)
        logger.info(f"Successfully extracted text from {file_path}")
        logger.info(f"Extracted text: {extracted_text[:200]}...")  # Show first 200 chars
        
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
    """Main function to process test PDF."""
    # Check if a file path was provided as a command line argument
    if len(sys.argv) > 1:
        # Use the provided file path
        pdf_file = sys.argv[1]
        if not os.path.exists(pdf_file):
            logger.error(f"File not found: {pdf_file}")
            sys.exit(1)
    else:
        # Create a test PDF if no file path was provided
        pdf_file = create_test_pdf()
    
    # Process the PDF
    process_soc2_report(pdf_file)
    
    logger.info("Test complete")

if __name__ == "__main__":
    main() 