#!/usr/bin/env python
"""List available Gemini models."""

import google.generativeai as genai
from app.core.config import settings

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)

print("Available Gemini models:")
print("="*60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✓ {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Description: {model.description}")
        print()
