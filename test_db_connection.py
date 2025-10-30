"""Test database connection"""
import sys
sys.path.insert(0, 'D:\\AiHr\\backend')

from app.db.database import SessionLocal
from app.models.candidate import Candidate

print("Testing database connection...")
db = SessionLocal()
try:
    # Try to query candidates table
    count = db.query(Candidate).count()
    print(f"✅ Database connected! Candidates count: {count}")
except Exception as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
