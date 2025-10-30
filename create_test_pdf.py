"""
Quick script to convert test resume to PDF
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

# Read the text resume
with open('D:\\AiHr\\test_resume_sarah_johnson.txt', 'r') as f:
    content = f.read()

# Create PDF
pdf_path = 'D:\\AiHr\\test_resume_sarah_johnson.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=letter)
story = []

# Styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=16,
    textColor='#000000',
    spaceAfter=12,
)
normal_style = styles['BodyText']

# Split content into paragraphs
paragraphs = content.split('\n\n')

for para in paragraphs:
    if para.strip():
        # First paragraph is the name (title)
        if para.startswith('SARAH JOHNSON'):
            story.append(Paragraph(para.replace('\n', '<br/>'), title_style))
        else:
            story.append(Paragraph(para.replace('\n', '<br/>'), normal_style))
        story.append(Spacer(1, 0.2*inch))

# Build PDF
doc.build(story)
print(f"✅ PDF created: {pdf_path}")
