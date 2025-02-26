#!/usr/bin/env python3
"""
Generate a sample SOC2 report PDF for testing.
"""

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    print("Please install reportlab: pip install reportlab")
    exit(1)

def generate_sample_soc2_report():
    """Generate a sample SOC2 report PDF."""
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        "sample_data/sample_soc2_report.pdf",
        pagesize=letter,
        title="Sample SOC2 Report",
        author="Test Organization"
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    subheading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Title
    content.append(Paragraph("SOC 2 Type II Report", title_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Test Organization, Inc.", heading_style))
    content.append(Paragraph("For the period January 1, 2023 to December 31, 2023", normal_style))
    content.append(Spacer(1, 24))
    
    # Table of Contents
    content.append(Paragraph("Table of Contents", heading_style))
    content.append(Spacer(1, 12))
    toc_data = [
        ["Section", "Page"],
        ["I. Independent Service Auditor's Report", "3"],
        ["II. Management's Assertion", "5"],
        ["III. Description of the System", "7"],
        ["IV. Control Objectives and Related Controls", "15"],
        ["V. Tests of Controls and Results", "25"],
    ]
    toc_table = Table(toc_data, colWidths=[350, 50])
    toc_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    content.append(toc_table)
    content.append(Spacer(1, 24))
    
    # Section I
    content.append(Paragraph("I. Independent Service Auditor's Report", heading_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("To the Management of Test Organization, Inc.:", normal_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("We have examined Test Organization's description of its cloud platform system for processing user entities' transactions throughout the period January 1, 2023 to December 31, 2023 (the \"Description\") and the suitability of the design and operating effectiveness of controls included in the Description to achieve the related control objectives, also included in the Description.", normal_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("In our opinion, in all material respects, based on the criteria described in Test Organization's assertion:", normal_style))
    content.append(Spacer(1, 12))
    
    # Section II
    content.append(Paragraph("II. Management's Assertion", heading_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("We have prepared the description of Test Organization's cloud platform system for processing user entities' transactions throughout the period January 1, 2023 to December 31, 2023 for user entities of the system and their auditors who have a sufficient understanding to consider it, along with other information, including information about controls implemented by user entities of the system themselves.", normal_style))
    content.append(Spacer(1, 12))
    
    # Section III
    content.append(Paragraph("III. Description of the System", heading_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Company Background", subheading_style))
    content.append(Paragraph("Test Organization, Inc. is a cloud service provider that offers infrastructure, platform, and software services to businesses of all sizes. Founded in 2010, Test Organization has grown to serve over 5,000 customers worldwide.", normal_style))
    content.append(Spacer(1, 12))
    
    # Section IV
    content.append(Paragraph("IV. Control Objectives and Related Controls", heading_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("The following control objectives and related controls are included in the Description:", normal_style))
    content.append(Spacer(1, 12))
    
    # Control objectives
    control_objectives = [
        "1. Control Environment",
        "2. Communication and Information",
        "3. Risk Assessment",
        "4. Monitoring Activities",
        "5. Control Activities",
        "6. Logical and Physical Access Controls",
        "7. System Operations",
        "8. Change Management",
        "9. Risk Mitigation",
    ]
    
    for objective in control_objectives:
        content.append(Paragraph(objective, normal_style))
        content.append(Spacer(1, 6))
    
    content.append(Spacer(1, 12))
    
    # Section V
    content.append(Paragraph("V. Tests of Controls and Results", heading_style))
    content.append(Spacer(1, 12))
    content.append(Paragraph("Our tests of the operating effectiveness of controls included such tests as were considered necessary in the circumstances to evaluate whether those controls, and the extent of compliance with them, were sufficient to provide reasonable, but not absolute, assurance that the control objectives specified in the Description were achieved during the period from January 1, 2023 to December 31, 2023.", normal_style))
    content.append(Spacer(1, 12))
    
    # Sample control test
    test_data = [
        ["Control Objective", "Control Activity", "Test Procedure", "Test Result"],
        ["Logical Access", "Access to systems requires multi-factor authentication", "Inspected authentication configurations and tested login process", "No exceptions noted"],
        ["Change Management", "Changes to production systems require approval", "Examined change tickets for proper approval", "No exceptions noted"],
        ["Data Protection", "Data is encrypted at rest and in transit", "Inspected encryption configurations", "No exceptions noted"],
    ]
    test_table = Table(test_data, colWidths=[100, 150, 150, 100])
    test_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    content.append(test_table)
    
    # Build the PDF
    doc.build(content)
    print("Sample SOC2 report generated: sample_data/sample_soc2_report.pdf")

if __name__ == "__main__":
    generate_sample_soc2_report() 