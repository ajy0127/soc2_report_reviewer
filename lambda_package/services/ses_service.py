"""
SES service for the SOC 2 Report Analysis Tool.
"""

import logging
import boto3
import os
import json
from botocore.exceptions import ClientError
from utils.error_handling import SESError, retry

logger = logging.getLogger()

@retry(max_attempts=3, exceptions=(ClientError,))
def send_email(recipient, report_name, analysis_result):
    """
    Send an email notification with the analysis results.
    
    Args:
        recipient (str): Email recipient
        report_name (str): Name of the report
        analysis_result (dict): Analysis result
        
    Returns:
        bool: True if the email was sent successfully
        
    Raises:
        SESError: If there's an error sending the email
    """
    try:
        ses_client = boto3.client('ses')
        
        # Get sender email from environment variable or use default
        sender = os.environ.get('SENDER_EMAIL', 'no-reply@example.com')
        
        # Create email subject
        subject = f"SOC 2 Report Analysis: {report_name}"
        
        # Create email body
        body_html = create_email_body_html(report_name, analysis_result)
        body_text = create_email_body_text(report_name, analysis_result)
        
        # Send email
        response = ses_client.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Text': {
                        'Data': body_text
                    },
                    'Html': {
                        'Data': body_html
                    }
                }
            }
        )
        
        logger.info(f"Email sent to {recipient} with message ID: {response['MessageId']}")
        return True
        
    except ClientError as e:
        error_message = f"Error sending email: {str(e)}"
        logger.error(error_message)
        raise SESError(error_message)

def create_email_body_html(report_name, analysis_result):
    """
    Create HTML email body with analysis results.
    
    Args:
        report_name (str): Name of the report
        analysis_result (dict): Analysis result
        
    Returns:
        str: HTML email body
    """
    # Extract data from analysis result
    executive_summary = analysis_result.get('executive_summary', 'No summary available')
    quality_rating = analysis_result.get('quality_rating', 0)
    controls = analysis_result.get('controls', [])
    framework_mappings = analysis_result.get('framework_mappings', {})
    identified_gaps = analysis_result.get('identified_gaps', [])
    
    # Create HTML body
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .summary {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; }}
            .rating {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
            .rating-value {{ color: #e67e22; }}
            .section {{ margin-bottom: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .gap {{ background-color: #fff8f8; padding: 10px; border-left: 4px solid #e74c3c; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SOC 2 Report Analysis</h1>
            <p>Report: <strong>{report_name}</strong></p>
            
            <div class="section">
                <h2>Executive Summary</h2>
                <div class="summary">
                    <p>{executive_summary}</p>
                </div>
                <p class="rating">Quality Rating: <span class="rating-value">{quality_rating}/5</span></p>
            </div>
            
            <div class="section">
                <h2>Key Controls</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Description</th>
                        <th>Effectiveness</th>
                    </tr>
    """
    
    # Add controls to the table
    for control in controls:
        control_id = control.get('id', 'N/A')
        description = control.get('description', 'No description available')
        effectiveness = control.get('effectiveness', 'Unknown')
        
        html += f"""
                    <tr>
                        <td>{control_id}</td>
                        <td>{description}</td>
                        <td>{effectiveness}</td>
                    </tr>
        """
    
    html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Framework Mappings</h2>
    """
    
    # Add framework mappings
    for framework, mappings in framework_mappings.items():
        if isinstance(mappings, list):
            html += f"""
                <h3>{framework}</h3>
                <p>{', '.join(mappings)}</p>
            """
        else:
            html += f"""
                <h3>{framework}</h3>
                <p>{str(mappings)}</p>
            """
    
    html += """
            </div>
            
            <div class="section">
                <h2>Identified Gaps</h2>
    """
    
    # Add identified gaps
    if identified_gaps:
        for gap in identified_gaps:
            html += f"""
                <div class="gap">
                    <p>{gap}</p>
                </div>
            """
    else:
        html += """
                <p>No significant gaps identified.</p>
        """
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def create_email_body_text(report_name, analysis_result):
    """
    Create plain text email body with analysis results.
    
    Args:
        report_name (str): Name of the report
        analysis_result (dict): Analysis result
        
    Returns:
        str: Plain text email body
    """
    # Extract data from analysis result
    executive_summary = analysis_result.get('executive_summary', 'No summary available')
    quality_rating = analysis_result.get('quality_rating', 0)
    controls = analysis_result.get('controls', [])
    framework_mappings = analysis_result.get('framework_mappings', {})
    identified_gaps = analysis_result.get('identified_gaps', [])
    
    # Create text body
    text = f"""
SOC 2 Report Analysis
=====================

Report: {report_name}

Executive Summary
----------------
{executive_summary}

Quality Rating: {quality_rating}/5

Key Controls
-----------
"""
    
    # Add controls
    for control in controls:
        control_id = control.get('id', 'N/A')
        description = control.get('description', 'No description available')
        effectiveness = control.get('effectiveness', 'Unknown')
        
        text += f"""
* {control_id}: {description} - {effectiveness}
"""
    
    text += """
Framework Mappings
-----------------
"""
    
    # Add framework mappings
    for framework, mappings in framework_mappings.items():
        if isinstance(mappings, list):
            text += f"""
{framework}: {', '.join(mappings)}
"""
        else:
            text += f"""
{framework}: {str(mappings)}
"""
    
    text += """
Identified Gaps
--------------
"""
    
    # Add identified gaps
    if identified_gaps:
        for gap in identified_gaps:
            text += f"""
* {gap}
"""
    else:
        text += """
No significant gaps identified.
"""
    
    return text 

# Alias for send_email to match the import in the Lambda handler
send_notification = send_email 