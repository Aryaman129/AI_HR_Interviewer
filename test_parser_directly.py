"""Debug script to test resume parser directly"""
import sys
sys.path.insert(0, 'D:\\AiHr\\backend')

from app.services.resume_parser import get_resume_parser

print("Loading resume parser...")
parser = get_resume_parser()
print("✅ Parser loaded")

print("\nParsing test resume...")
result = parser.parse('D:\\AiHr\\test_resume_sarah_johnson.pdf')
print(f"✅ Parsed! Email: {result['email']}")
print(f"Skills: {result['skills']}")
print(f"Embedding dimensions: {len(result['resume_embedding'])}")
