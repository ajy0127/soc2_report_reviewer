import json
import os
import logging
from services.s3_service import S3Service
from services.textract_service import TextractService
from services.bedrock_service import BedrockService
from services.ses_service import SESService
from utils.validation import validate_event
from utils.error_handling import handle_error

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize service instances
# These services handle specific AWS service interactions
s3_service = S3Service()        # Handles S3 operations (get/put objects)
textract_service = TextractService()  # Handles text extraction from PDFs
bedrock_service = BedrockService()    # Handles AI analysis with Amazon Bedrock
ses_service = SESService()      # Handles email notifications via SES

def lambda_handler(event, context):
    """
    Main Lambda handler function for SOC2-Analyzer.
    
    This function is the entry point for the Lambda function and orchestrates the entire
    workflow for analyzing SOC2 reports:
    1. Validates the incoming event
    2. Retrieves the PDF file from S3
    3. Extracts text from the PDF using Textract
    4. Analyzes the text using Bedrock AI
    5. Saves the analysis results to S3
    6. Sends a notification email with the results
    
    Args:
        event (dict): The event dict containing the S3 event details
        context (LambdaContext): The Lambda context object
        
    Returns:
        dict: Response containing status code and body
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Step 1: Validate the incoming event
        # This extracts the bucket name and object key from the event
        bucket_name, object_key = validate_event(event)
        logger.info(f"Processing file {object_key} from bucket {bucket_name}")
        
        # Step 2: Get the file from S3
        # Retrieves the PDF content as bytes
        pdf_content = s3_service.get_object(bucket_name, object_key)
        
        # Step 3: Extract text from the PDF using Textract
        # Converts the PDF content to plain text
        extracted_text = textract_service.extract_text(pdf_content)
        logger.info(f"Successfully extracted text from {object_key}")
        
        # Step 4: Analyze the text using Bedrock
        # Sends the extracted text to Bedrock for AI analysis
        analysis_result = bedrock_service.analyze_soc2_report(extracted_text)
        logger.info("Successfully analyzed SOC2 report")
        
        # Step 5: Save the analysis result to S3
        # Constructs the output key and saves the JSON result
        output_bucket = os.environ.get('OUTPUT_BUCKET')
        output_key = f"results/{object_key.split('/')[-1].replace('.pdf', '')}_analysis.json"
        s3_service.put_object(output_bucket, output_key, json.dumps(analysis_result))
        logger.info(f"Saved analysis result to s3://{output_bucket}/{output_key}")
        
        # Step 6: Send notification email
        # Generates a presigned URL and sends an email with the results
        notification_email = os.environ.get('NOTIFICATION_EMAIL')
        result_url = s3_service.generate_presigned_url(output_bucket, output_key)
        ses_service.send_notification(
            notification_email, 
            f"SOC2 Analysis Complete: {object_key}",
            analysis_result,
            result_url
        )
        logger.info(f"Sent notification email to {notification_email}")
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'SOC2 report analysis completed successfully',
                'input_file': object_key,
                'result_file': output_key
            })
        }
        
    except Exception as e:
        # Handle any errors that occur during processing
        # The handle_error function returns appropriate HTTP responses based on error type
        logger.error(f"Error processing SOC2 report: {str(e)}", exc_info=True)
        return handle_error(e) 