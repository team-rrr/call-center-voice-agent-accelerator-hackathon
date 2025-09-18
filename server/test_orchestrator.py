"""
Simple test script to demonstrate calling the orchestrator endpoint.
"""

import requests
import json

def test_orchestrator_endpoint():
    """Test the orchestrator API endpoint."""
    
    # Endpoint URL (adjust if running on different port)
    url = "http://127.0.0.1:8000/api/orchestrator"
    
    # Test message matching your sample interaction
    test_data = {
        "message": "Hi, I'm taking my mother to her cardiology appointment next week. What should I bring?",
        "session_id": "test_session_123",
        "patient_context": {
            "patient_id": "patient_001",
            "appointment_type": "cardiology"
        }
    }
    
    try:
        print("Sending request to orchestrator...")
        print(f"Message: {test_data['message']}")
        print()
        
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            print("🎉 SUCCESS! Orchestrator Response:")
            print("=" * 80)
            
            # Format the main response content
            if result.get('success'):
                response_text = result.get('response', '')
                
                # Clean up unicode characters for better display
                response_text = response_text.replace('\\u2019', "'").replace('\\u201c', '"').replace('\\u201d', '"')
                
                print("📋 ORCHESTRATED RESPONSE:")
                print("-" * 40)
                print(response_text)
                print()
                
                # Display session information
                print("📊 SESSION DETAILS:")
                print("-" * 40)
                print(f"✅ Session ID: {result.get('session_id', 'N/A')}")
                print(f"🧵 Thread ID: {result.get('thread_id', 'N/A')}")
                print(f"🏃 Run ID: {result.get('run_id', 'N/A')}")
                print()
                
                # Extract and highlight key sections
                if 'InfoAgent' in response_text:
                    print("🔍 AGENTS INVOLVED:")
                    print("-" * 40)
                    if 'InfoAgent' in response_text:
                        print("📚 InfoAgent: General medical guidance")
                    if 'PatientContextAgent' in response_text:
                        print("👤 PatientContextAgent: Patient-specific insights")
                    if 'ActionAgent' in response_text:
                        print("✅ ActionAgent: Actionable checklist")
                    print()
                
            else:
                print("❌ REQUEST FAILED:")
                print("-" * 40)
                print(f"Error: {result.get('error', 'Unknown error')}")
                print(f"Response: {result.get('response', 'No response')}")
                
        else:
            print("❌ HTTP ERROR:")
            print("-" * 40)
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print("Make sure the server is running on http://localhost:8000")

if __name__ == "__main__":
    test_orchestrator_endpoint()