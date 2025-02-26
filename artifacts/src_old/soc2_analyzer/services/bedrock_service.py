"""
Bedrock service for the SOC 2 Report Analysis Tool.
"""

import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
from soc2_analyzer.utils.error_handling import BedrockError, ValidationError, retry
from soc2_analyzer.utils.validation import validate_analysis_result, validate_json_format

logger = logging.getLogger()

# Get model ID from environment variable or use default
MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')

@retry(max_attempts=3, delay=2, backoff=2, exceptions=(ClientError, json.JSONDecodeError))
def analyze_text(text):
    """
    Analyze text using Amazon Bedrock.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        dict: Analysis result
        
    Raises:
        BedrockError: If analysis fails
        ValidationError: If the analysis result is invalid
    """
    bedrock_client = boto3.client('bedrock-runtime')
    
    try:
        logger.info(f"Starting AI analysis with model: {MODEL_ID}")
        
        # Truncate text if it's too long
        # This is a simple approach - a more sophisticated approach would be to
        # chunk the text and analyze each chunk
        max_text_length = 100000  # Adjust based on model limits
        if len(text) > max_text_length:
            logger.warning(f"Text is too long ({len(text)} chars), truncating to {max_text_length} chars")
            text = text[:max_text_length]
        
        # Create prompt
        prompt = create_prompt(text)
        
        # Invoke model
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 4000,
                'temperature': 0.2,
                'system': "You are a cybersecurity expert specializing in SOC 2 compliance. Your task is to analyze SOC 2 reports and extract key information.",
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        result_text = response_body['content'][0]['text']
        
        logger.info("AI analysis completed successfully")
        
        # Extract JSON from the response
        result_json = extract_json_from_response(result_text)
        
        # Validate the result structure
        validate_analysis_result(result_json)
        
        return result_json
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ModelTimeoutException':
            raise BedrockError(f"Model timeout: {error_message}")
        elif error_code == 'ModelStreamErrorException':
            raise BedrockError(f"Model stream error: {error_message}")
        elif error_code == 'ValidationException':
            raise BedrockError(f"Validation error: {error_message}")
        elif error_code == 'AccessDeniedException':
            raise BedrockError(f"Access denied: {error_message}")
        elif error_code == 'ThrottlingException':
            raise BedrockError(f"Throttling exception: {error_message}")
        else:
            raise BedrockError(f"Bedrock error: {error_code} - {error_message}")
    except json.JSONDecodeError as e:
        raise BedrockError(f"Error parsing JSON response: {str(e)}")
    except ValidationError:
        # Let ValidationError pass through without wrapping it
        raise
    except Exception as e:
        raise BedrockError(f"Error analyzing text: {str(e)}")

def create_prompt(text):
    """
    Create a prompt for the AI model.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        str: Prompt for the AI model
    """
    return f"""
    You are analyzing a SOC 2 report. Extract the following information and return it as a valid JSON object:

    1. scope: A brief description of the scope of the SOC 2 report.
    2. controls: An array of objects, each with a "name" and "status" field. Status should be either "Compliant" or "Non-compliant".
    3. cis_mapping: An object with two arrays - "mapped" (CIS controls that are covered) and "gaps" (CIS controls that are not covered).
    4. owasp_mapping: An object with two arrays - "mapped" (OWASP Top 10 items that are covered) and "gaps" (OWASP Top 10 items that are not covered).
    5. gaps: An array of strings describing any gaps or deficiencies in the controls.
    6. summary: A brief summary of the overall report.
    7. quality_rating: A number from 0 to 10 indicating the quality of the report.

    Return ONLY the JSON object without any additional text or explanation. The JSON should be properly formatted and valid.

    Here is the SOC 2 report text:
    {text}
    """

def extract_json_from_response(response_text):
    """
    Extract JSON from the model response.
    
    Args:
        response_text (str): Response text from the model
        
    Returns:
        dict: Extracted JSON
        
    Raises:
        BedrockError: If JSON extraction fails
    """
    try:
        # Try to parse the entire response as JSON
        if validate_json_format(response_text):
            return json.loads(response_text)
        
        # If that fails, look for JSON within the response
        # This handles cases where the model might add explanatory text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
            if validate_json_format(json_str):
                return json.loads(json_str)
        
        # If we still can't find valid JSON, try to extract JSON from code blocks
        # This handles cases where the model wraps JSON in markdown code blocks
        if '```json' in response_text:
            parts = response_text.split('```json')
            if len(parts) > 1:
                json_part = parts[1].split('```')[0].strip()
                if validate_json_format(json_part):
                    return json.loads(json_part)
        
        # If we still can't find valid JSON, raise an error
        raise BedrockError("Could not extract valid JSON from model response")
        
    except json.JSONDecodeError as e:
        raise BedrockError(f"Error parsing JSON from model response: {str(e)}")
    except Exception as e:
        raise BedrockError(f"Error extracting JSON from model response: {str(e)}") 