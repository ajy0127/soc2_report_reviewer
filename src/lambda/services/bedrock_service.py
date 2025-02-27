import boto3
import json
import logging
import os
from botocore.exceptions import ClientError

logger = logging.getLogger()

class BedrockService:
    """
    Service class for Amazon Bedrock operations.
    
    This class provides methods for analyzing SOC2 reports using Amazon Bedrock's
    AI models. It handles:
    - Creating prompts for the AI model
    - Invoking the model with appropriate parameters
    - Parsing and structuring the model's response
    """
    
    def __init__(self):
        """
        Initialize the Bedrock service with boto3 client.
        
        Creates a Bedrock runtime client using boto3 and retrieves the model ID
        from environment variables (with a default fallback to Claude 3 Sonnet).
        """
        self.bedrock_client = boto3.client('bedrock-runtime')
        # Get the model ID from environment variables or use a default
        self.model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    def analyze_soc2_report(self, text):
        """
        Analyzes a SOC2 report using Amazon Bedrock.
        
        This method is the main entry point for AI analysis. It:
        1. Truncates the text if it's too long for the model
        2. Creates a prompt for the model
        3. Invokes the model with the prompt
        4. Parses and structures the response
        
        Args:
            text (str): The extracted text from the SOC2 report
            
        Returns:
            dict: The structured analysis results
            
        Raises:
            ClientError: If the Bedrock service call fails
        """
        try:
            logger.info(f"Analyzing SOC2 report with Bedrock model: {self.model_id}")
            
            # Step 1: Truncate text if it's too long (model context limits)
            # Different models have different token limits
            max_tokens = 100000  # Adjust based on model limits
            if len(text) > max_tokens:
                logger.warning(f"Text is too long ({len(text)} chars), truncating to {max_tokens} chars")
                text = text[:max_tokens]
            
            # Step 2: Create the prompt for the model
            prompt = self._create_analysis_prompt(text)
            
            # Step 3: Call the Bedrock model
            response = self._invoke_model(prompt)
            
            # Step 4: Parse and structure the response
            analysis_result = self._parse_response(response)
            
            logger.info("Successfully analyzed SOC2 report")
            return analysis_result
            
        except ClientError as e:
            logger.error(f"Error analyzing SOC2 report with Bedrock: {str(e)}")
            raise
    
    def _create_analysis_prompt(self, text):
        """
        Creates the prompt for the Bedrock model.
        
        This method constructs a detailed prompt that instructs the AI model
        on how to analyze the SOC2 report. The prompt includes:
        - Instructions on what information to extract
        - The structure of the expected response
        - The actual SOC2 report text to analyze
        
        Args:
            text (str): The extracted text from the SOC2 report
            
        Returns:
            str: The formatted prompt
        """
        # Create a structured prompt with clear instructions
        # Using Claude's XML-style formatting for instructions and content
        prompt = f"""
        <instructions>
        You are a SOC2 report analysis expert. Analyze the following SOC2 report text and extract key information.
        Provide a structured analysis with the following sections:
        
        1. Report Overview
           - Service Organization name
           - Service Auditor name
           - Report Type (Type 1 or Type 2)
           - Report Period
           - Trust Services Criteria covered (Security, Availability, Processing Integrity, Confidentiality, Privacy)
        
        2. Scope and Boundaries
           - Systems and services in scope
           - Key components and infrastructure
           - Subservice organizations (if any)
        
        3. Controls Assessment
           - Summary of controls by Trust Services Category
           - Number of controls tested
           - Number of controls with exceptions or deficiencies
        
        4. Exceptions and Deficiencies
           - List all exceptions or deficiencies found
           - Severity assessment for each (High, Medium, Low)
           - Potential impact on the organization
        
        5. Auditor Opinion
           - Overall opinion (Unqualified, Qualified, Adverse, Disclaimer)
           - Key statements from the opinion section
        
        6. Risk Assessment
           - Key risks identified
           - Risk rating (High, Medium, Low)
           - Recommendations for risk mitigation
        
        7. Complementary User Entity Controls (CUECs)
           - List of important CUECs mentioned
           - Assessment of their criticality
        
        8. Summary and Recommendations
           - Overall assessment of the SOC2 report
           - Key strengths identified
           - Areas of concern
           - Specific recommendations for the organization reviewing this report
        
        Format your response as a JSON object with these sections as keys. For any information that cannot be determined from the text, use "Not specified" or "Unable to determine".
        </instructions>
        
        <soc2_report>
        {text}
        </soc2_report>
        """
        
        return prompt
    
    def _invoke_model(self, prompt):
        """
        Invokes the Bedrock model with the given prompt.
        
        This method handles the details of calling the Bedrock API with the
        appropriate parameters based on the model type. It supports:
        - Claude models (using the messages API format)
        - Other models (using a simpler prompt format)
        
        Args:
            prompt (str): The prompt for the model
            
        Returns:
            str: The model's response text
            
        Raises:
            ClientError: If the model invocation fails
        """
        # Prepare the request based on the model type
        # Different models have different API formats
        if self.model_id.startswith('anthropic.claude'):
            # Claude models use the messages format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "temperature": 0.2,  # Lower temperature for more deterministic responses
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        else:
            # Default format for other models
            request_body = {
                "prompt": prompt,
                "max_tokens": 4096,
                "temperature": 0.2
            }
        
        # Invoke the model with the prepared request
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response based on the model type
        response_body = json.loads(response.get('body').read())
        
        if self.model_id.startswith('anthropic.claude'):
            # Extract text from Claude's response format
            return response_body.get('content', [{}])[0].get('text', '')
        else:
            # Default parsing for other models
            return response_body.get('completion', '')
    
    def _parse_response(self, response_text):
        """
        Parses the model's response into a structured format.
        
        This method attempts to extract and parse JSON from the model's response.
        It handles several cases:
        1. Response is already valid JSON
        2. Response contains JSON embedded in text
        3. Response is not JSON-formatted
        
        Args:
            response_text (str): The model's response text
            
        Returns:
            dict: The structured analysis results
        """
        try:
            # Case 1: Try to parse as JSON directly
            # If the response is already a valid JSON object
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                return json.loads(response_text)
            
            # Case 2: If not valid JSON, extract JSON from the text
            # Find the first { and last } to extract a JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            
            # Case 3: If no JSON found, create a structured response manually
            logger.warning("Could not parse model response as JSON, creating structured format manually")
            
            # Create a basic structure with the raw response
            return {
                "raw_analysis": response_text,
                "parsing_note": "The model response could not be parsed as JSON. This is the raw analysis."
            }
            
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            logger.error(f"Error parsing model response as JSON: {str(e)}")
            return {
                "raw_analysis": response_text,
                "parsing_error": str(e)
            } 