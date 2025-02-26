#!/usr/bin/env python3
"""
Script to convert the Markdown deployment guide to a PDF for easy printing.
Requires: pip install markdown weasyprint
"""

import markdown
import os
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# CSS for styling the PDF
CSS_CONTENT = """
@page {
    margin: 1cm;
    @top-center {
        content: "SOC 2 Report Analysis Tool - Deployment Guide";
        font-family: sans-serif;
        font-size: 10pt;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-family: sans-serif;
        font-size: 10pt;
    }
}

body {
    font-family: sans-serif;
    font-size: 12pt;
    line-height: 1.5;
    margin: 0;
    padding: 0;
}

h1 {
    color: #0066cc;
    font-size: 24pt;
    margin-top: 20pt;
    margin-bottom: 10pt;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    color: #0066cc;
    font-size: 18pt;
    margin-top: 15pt;
    margin-bottom: 8pt;
}

h3 {
    color: #333333;
    font-size: 14pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

p {
    margin-bottom: 8pt;
}

ul, ol {
    margin-bottom: 8pt;
}

li {
    margin-bottom: 4pt;
}

code {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 3px;
    font-family: monospace;
    padding: 2px 4px;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 20pt 0;
}

.footer {
    font-size: 10pt;
    font-style: italic;
    color: #666;
    margin-top: 20pt;
}
"""

def convert_md_to_pdf(md_file, pdf_file):
    """Convert a Markdown file to PDF."""
    print(f"Converting {md_file} to {pdf_file}...")
    
    # Read the Markdown file
    with open(md_file, 'r') as f:
        md_content = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Add HTML header and footer
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>SOC 2 Report Analysis Tool - Deployment Guide</title>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Create CSS
    css = CSS(string=CSS_CONTENT, font_config=font_config)
    
    # Generate PDF
    HTML(string=html_doc).write_pdf(pdf_file, stylesheets=[css], font_config=font_config)
    
    print(f"PDF created successfully: {pdf_file}")

if __name__ == "__main__":
    # File paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(current_dir, "SOC2_Analysis_Tool_Deployment_Guide.md")
    pdf_file = os.path.join(current_dir, "SOC2_Analysis_Tool_Deployment_Guide.pdf")
    
    # Convert Markdown to PDF
    convert_md_to_pdf(md_file, pdf_file)
    
    print("\nTo install required dependencies:")
    print("pip install markdown weasyprint") 