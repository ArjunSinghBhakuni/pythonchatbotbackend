#!/usr/bin/env python3
"""
Test script for the new Gemini-based backend
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "uploads/test.pdf"  # You can add a test PDF here

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_knowledge_stats():
    """Test knowledge stats endpoint"""
    print("\n🔍 Testing knowledge stats...")
    try:
        response = requests.get(f"{BASE_URL}/knowledge-stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Knowledge stats retrieved")
            print(f"   Total chunks: {stats.get('total_chunks', 0)}")
            print(f"   Status: {stats.get('status', 'unknown')}")
        else:
            print(f"❌ Knowledge stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Knowledge stats error: {e}")

def test_chat():
    """Test chat endpoint"""
    print("\n🔍 Testing chat endpoint...")
    try:
        data = {"message": "What is the DPDP Act?"}
        response = requests.post(f"{BASE_URL}/chat", data=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat test passed")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Chat test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat test error: {e}")

def test_risk_assessment():
    """Test risk assessment endpoint"""
    print("\n🔍 Testing risk assessment...")
    try:
        data = {"query": "What are the risks of collecting personal data without consent?"}
        response = requests.post(f"{BASE_URL}/risk-assessment", data=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Risk assessment test passed")
            print(f"   Risk level: {result.get('risk_level', 'Unknown')}")
            print(f"   Analysis: {result.get('analysis', 'No analysis')[:100]}...")
        else:
            print(f"❌ Risk assessment test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Risk assessment test error: {e}")

def test_pdf_upload():
    """Test PDF upload endpoint (if test PDF exists)"""
    if not os.path.exists(TEST_PDF_PATH):
        print(f"\n⚠️  Skipping PDF upload test - no test PDF found at {TEST_PDF_PATH}")
        return
    
    print(f"\n🔍 Testing PDF upload with {TEST_PDF_PATH}...")
    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/upload-pdf", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF upload test passed")
            print(f"   Message: {result.get('message', 'No message')}")
            print(f"   Chunks processed: {result.get('chunks_processed', 0)}")
        else:
            print(f"❌ PDF upload test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ PDF upload test error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Gemini Backend Tests")
    print("=" * 50)
    
    test_health()
    test_knowledge_stats()
    test_chat()
    test_risk_assessment()
    test_pdf_upload()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main()




