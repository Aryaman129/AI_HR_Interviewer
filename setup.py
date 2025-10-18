"""
Setup script for AI HR Interviewer system
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False
    return True

def setup_directories():
    """Create necessary directories"""
    print("Setting up directories...")
    
    directories = [
        "backend/data/resumes",
        "backend/data/vectorstore", 
        "backend/models",
        "frontend/audio_logs",
        "frontend/chat_logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def download_models():
    """Download required AI models"""
    print("Setting up AI models...")
    
    try:
        # Check if Ollama is running
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running!")
            
            # Check if llama3 is available
            if "llama3:latest" in result.stdout:
                print("✅ Llama3 model is available!")
            else:
                print("📥 Downloading Llama3 model...")
                subprocess.run(["ollama", "pull", "llama3:latest"])
        else:
            print("❌ Ollama is not running. Please start Ollama first.")
            return False
            
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        return False
    
    return True

def generate_sample_data():
    """Generate sample resumes and job requirements"""
    print("Generating sample data...")
    
    try:
        from utils.resume_collector import ResumeCollector
        collector = ResumeCollector()
        resumes = collector.generate_sample_resumes()
        jobs = collector.create_job_requirements_samples()
        
        print(f"✅ Generated {len(resumes)} sample resumes")
        print(f"✅ Generated {len(jobs)} sample job requirements")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up AI HR Interviewer System...")
    print("=" * 50)
    
    # Step 1: Setup directories
    if not setup_directories():
        print("❌ Failed to setup directories")
        return
    
    # Step 2: Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return
    
    # Step 3: Setup models
    if not download_models():
        print("⚠️ Model setup incomplete. You may need to setup Ollama manually.")
    
    # Step 4: Generate sample data
    if not generate_sample_data():
        print("⚠️ Sample data generation failed. You can generate it manually later.")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("\nTo start the application:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Run: streamlit run frontend/streamlit_app/app.py")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
