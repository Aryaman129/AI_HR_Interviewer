"""
Test resume upload API endpoint
"""
import requests
import json
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/v1/resumes/parse"
PDF_PATH = r"D:\AiHr\test_resume_sarah_johnson.pdf"

print("🧪 Testing Resume Upload API")
print(f"📄 File: {PDF_PATH}")
print(f"🌐 Endpoint: {API_URL}")
print("-" * 60)

# Check if file exists
if not Path(PDF_PATH).exists():
    print(f"❌ Error: File not found at {PDF_PATH}")
    exit(1)

# Upload resume
try:
    with open(PDF_PATH, 'rb') as f:
        files = {'file': ('test_resume_sarah_johnson.pdf', f, 'application/pdf')}
        
        print("⏳ Uploading resume...")
        response = requests.post(API_URL, files=files, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS! Resume parsed and stored")
            print("\n📋 Response Data:")
            print(json.dumps(data, indent=2))
            
            # Extract key info
            print("\n" + "="*60)
            print("🎯 KEY INFORMATION:")
            print(f"  • Candidate ID: {data.get('candidate_id')}")
            print(f"  • Resume ID: {data.get('resume_id')}")
            print(f"  • Email: {data.get('email')}")
            print(f"  • Name: {data.get('full_name')}")
            print(f"  • Embeddings Generated: {data.get('embeddings_generated')}")
            
            if 'parsed_data' in data:
                pd = data['parsed_data']
                tech_skills = pd.get('skills', {}).get('technical', [])
                print(f"  • Technical Skills: {len(tech_skills)} found")
                print(f"    - {', '.join(tech_skills[:5])}{'...' if len(tech_skills) > 5 else ''}")
                print(f"  • Work Experience: {pd.get('total_experience_years', 0)} positions")
                print(f"  • Education: {len(pd.get('education', []))} entries")
            
            print("="*60)
            
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("❌ Error: Could not connect to API. Is the server running?")
    print("   Try: cd D:\\AiHr\\backend && python -m uvicorn app.main:app --reload")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
