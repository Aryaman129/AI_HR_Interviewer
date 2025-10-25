"""
Simple script to run the FastAPI application
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import and run the application
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
