#!/usr/bin/env python3
"""
Test script for Risk Assessment endpoint
"""

import requests
import json
import time

def test_risk_assessment():
    """Test the risk assessment endpoint"""
    
    # Wait for backend to start
    print("Waiting for backend to start...")
    time.sleep(10)
    
    # Test data
    test_query = "Our e-commerce app collects customer payment details, purchase history, and browsing behavior. We share this data with advertising partners and use it for targeted marketing without explicit user consent. What are the compliance risks?"
    
    # Test the endpoint
    url = "http://localhost:8000/risk-assessment"
    data = {
        "query": test_query
    }
    
    print(f"Testing Risk Assessment with query: {test_query[:50]}...")
    print("=" * 60)
    
    try:
        response = requests.post(url, data=data, timeout=180)  # 3 minutes timeout
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCESS! Risk Assessment Response:")
            print(f"Analysis: {result.get('analysis', 'N/A')}")
            print(f"Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"Risks: {result.get('risks', [])}")
            print(f"Legal Implications: {result.get('legal_implications', [])}")
            print(f"Technical Considerations: {result.get('technical_considerations', [])}")
            print(f"Recommendations: {result.get('recommendations', [])}")
            print(f"Sources: {len(result.get('sources', []))} chunks found")
            
            # Check if we got meaningful content
            if result.get('analysis') and len(result.get('analysis', '')) > 50:
                print("\n🎯 SUCCESS: Got comprehensive risk assessment!")
            else:
                print("\n⚠️  WARNING: Response seems incomplete")
                
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out (3 minutes)")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_risk_assessment()






