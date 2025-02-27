import json
import os
import logging
from services.s3_service import S3Service
from services.ocrmypdf_service import OCRmyPDFService
from services.bedrock_service import BedrockService
from services.ses_service import SESService
from utils.validation import validate_event, validate_pdf_file, ValidationError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, _context):
    """
    Lambda function handler for SOC2 report analysis.
    
    Args:
        event (dict): Lambda event containing S3 bucket and key information
        _context (LambdaContext): Lambda context (unused)
        
    Returns:
        dict: Response containing status and analysis results
    """
    try:
        logger.info("Starting SOC2 report analysis")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Initialize services
        s3_service = S3Service()
        ocrmypdf_service = OCRmyPDFService()
        bedrock_service = BedrockService()
        ses_service = SESService()
        
        # Validate the event and get bucket and key
        try:
            bucket, key = validate_event(event)
        except ValidationError as e:
            logger.warning(f"Event validation failed: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f"Invalid event: {str(e)}"
                })
            }
            
        logger.info(f"Processing file s3://{bucket}/{key}")
        
        # Get the PDF content from S3
        pdf_content = s3_service.get_object(bucket, key)
        
        # Validate the PDF file
        try:
            validate_pdf_file(pdf_content)
            logger.info("PDF validation successful")
        except ValidationError as e:
            logger.warning(f"PDF validation failed: {str(e)}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f"Invalid PDF file: {str(e)}"
                })
            }
        
        # Extract text from PDF using OCRmyPDF
        extracted_text = ocrmypdf_service.extract_text(pdf_content)
        logger.info(f"Successfully extracted text from PDF")
        
        # Analyze the text with Bedrock
        analysis_result = bedrock_service.analyze_soc2_report(extracted_text)
        logger.info("Successfully analyzed SOC2 report")
        
        # Save analysis result to S3
        output_key = f"results/{os.path.basename(key).replace('.pdf', '')}_analysis.json"
        s3_service.put_object(
            os.environ['OUTPUT_BUCKET'],
            output_key,
            json.dumps(analysis_result, indent=2)
        )
        
        # Generate a presigned URL for the result
        result_url = s3_service.generate_presigned_url(
            os.environ['OUTPUT_BUCKET'],
            output_key
        )
        
        # Send notification email
        ses_service.send_notification(
            os.environ['NOTIFICATION_EMAIL'],
            f"SOC2 Analysis Complete: {os.path.basename(key)}",
            analysis_result,
            result_url
        )
        
        logger.info("SOC2 report analysis complete")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SOC2 report analysis completed successfully',
                'result_url': result_url
            })
        }
        
    except Exception as e:
        error_msg = f"Error processing SOC2 report: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        } 