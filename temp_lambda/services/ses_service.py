import boto3
import json
import logging
import os
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger()

class SESService:
    """
    Service class for Amazon SES operations.
    
    This class provides methods for sending email notifications using Amazon SES.
    It handles:
    - Creating HTML email content with analysis results
    - Formatting emails with proper MIME types
    - Attaching JSON results as an attachment
    - Sending emails via Amazon SES
    """
    
    def __init__(self):
        """
        Initialize the SES service with boto3 client.
        
        Creates an SES client using boto3 and retrieves the sender email
        from environment variables.
        """
        self.ses_client = boto3.client('ses')
        # Get the sender email from environment variables
        # This email must be verified in SES
        self.sender_email = os.environ.get('NOTIFICATION_EMAIL')
    
    def send_notification(self, recipient_email, subject, analysis_result, result_url):
        """
        Sends a notification email with the analysis results.
        
        This method creates and sends an HTML email with a summary of the
        analysis results and a link to the full results. It also attaches
        the complete JSON results as an attachment.
        
        Args:
            recipient_email (str): The recipient's email address
            subject (str): The email subject
            analysis_result (dict): The analysis results
            result_url (str): The URL to the full analysis results
            
        Returns:
            dict: The SES response
            
        Raises:
            ClientError: If the email cannot be sent
        """
        try:
            logger.info(f"Sending notification email to {recipient_email}")
            
            # Step 1: Create the email content
            html_body = self._create_html_email(analysis_result, result_url)
            
            # Step 2: Create a multipart/mixed parent container
            # This allows for both HTML content and attachments
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Step 3: Create a multipart/alternative child container
            # This would allow for both HTML and plain text versions
            # (though we're only using HTML here)
            msg_body = MIMEMultipart('alternative')
            
            # Step 4: Attach the HTML part
            html_part = MIMEText(html_body, 'html')
            msg_body.attach(html_part)
            
            # Step 5: Attach the message body to the parent container
            msg.attach(msg_body)
            
            # Step 6: Attach the JSON results as an attachment
            # This provides the complete results in a machine-readable format
            attachment = MIMEApplication(json.dumps(analysis_result, indent=2).encode('utf-8'))
            attachment.add_header('Content-Disposition', 'attachment', filename='soc2_analysis_results.json')
            msg.attach(attachment)
            
            # Step 7: Send the email via SES
            response = self.ses_client.send_raw_email(
                Source=self.sender_email,
                Destinations=[recipient_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            logger.info(f"Email sent successfully: {response['MessageId']}")
            return response
            
        except ClientError as e:
            logger.error(f"Error sending email: {str(e)}")
            raise
    
    def _create_html_email(self, analysis_result, result_url):
        """
        Creates the HTML content for the email.
        
        This method generates a formatted HTML email with key information
        from the analysis results. It includes:
        - Report overview information
        - Exceptions and deficiencies (if any)
        - Summary and recommendations
        - A link to the full results
        
        Args:
            analysis_result (dict): The analysis results
            result_url (str): The URL to the full analysis results
            
        Returns:
            str: The HTML content
        """
        # Extract key information from the analysis result
        # These sections correspond to the structure defined in the Bedrock prompt
        report_overview = analysis_result.get('Report Overview', {})
        exceptions = analysis_result.get('Exceptions and Deficiencies', {})
        summary = analysis_result.get('Summary and Recommendations', {})
        
        # Create the HTML content with CSS styling
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                .section {{ margin-bottom: 20px; }}
                .highlight {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; }}
                .warning {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; }}
                .danger {{ background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; }}
                .success {{ background-color: #d4edda; padding: 15px; border-left: 4px solid #28a745; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; 
                          text-decoration: none; border-radius: 4px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SOC2 Report Analysis Results</h1>
                
                <div class="section highlight">
                    <h2>Report Overview</h2>
                    <p><strong>Service Organization:</strong> {report_overview.get('Service Organization name', 'Not specified')}</p>
                    <p><strong>Service Auditor:</strong> {report_overview.get('Service Auditor name', 'Not specified')}</p>
                    <p><strong>Report Type:</strong> {report_overview.get('Report Type', 'Not specified')}</p>
                    <p><strong>Report Period:</strong> {report_overview.get('Report Period', 'Not specified')}</p>
                </div>
        """
        
        # Add exceptions section if there are any
        if exceptions and not isinstance(exceptions, str):
            html += f"""
                <div class="section warning">
                    <h2>Exceptions and Deficiencies</h2>
            """
            
            # Check if exceptions is a list
            if isinstance(exceptions.get('List all exceptions or deficiencies found'), list):
                exception_list = exceptions.get('List all exceptions or deficiencies found', [])
                if exception_list:
                    html += "<ul>"
                    for exception in exception_list:
                        html += f"<li>{exception}</li>"
                    html += "</ul>"
                else:
                    html += "<p>No exceptions or deficiencies found.</p>"
            else:
                html += f"<p>{exceptions.get('List all exceptions or deficiencies found', 'No exceptions or deficiencies found.')}</p>"
                
            html += """
                </div>
            """
        
        # Add summary section
        if summary and not isinstance(summary, str):
            html += f"""
                <div class="section success">
                    <h2>Summary and Recommendations</h2>
                    <p><strong>Overall Assessment:</strong> {summary.get('Overall assessment of the SOC2 report', 'Not provided')}</p>
                    
                    <h3>Key Strengths:</h3>
                    <p>{summary.get('Key strengths identified', 'Not provided')}</p>
                    
                    <h3>Areas of Concern:</h3>
                    <p>{summary.get('Areas of concern', 'Not provided')}</p>
                    
                    <h3>Recommendations:</h3>
                    <p>{summary.get('Specific recommendations for the organization reviewing this report', 'Not provided')}</p>
                </div>
            """
        
        # Add link to full results
        html += f"""
                <div class="section">
                    <h2>Full Analysis Results</h2>
                    <p>Click the button below to view the complete analysis results:</p>
                    <a href="{result_url}" class="button">View Full Results</a>
                </div>
                
                <div class="section">
                    <p>This is an automated analysis generated by the SOC2-Analyzer system. 
                    Please review the full results for a comprehensive understanding of the SOC2 report.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html 