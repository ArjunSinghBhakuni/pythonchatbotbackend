#!/usr/bin/env python3
"""
Startup script for the Gemini-based backend
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("🚀 Starting Gemini AI Backend...")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCk1XOPzJ8tTBTczHPhILjjEtzjAuGKLq4")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        print("   Please set GEMINI_API_KEY in your .env file")
        exit(1)
    
    print(f"✅ Using Gemini API Key: {api_key[:10]}...")
    print("✅ Starting server on http://localhost:8000")
    print("✅ API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "gemini_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )




