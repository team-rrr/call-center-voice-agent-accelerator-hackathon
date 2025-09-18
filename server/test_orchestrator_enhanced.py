"""
Enhanced test script with multiple scenarios for the orchestrator endpoint.
"""

import requests
import json

def print_separator(title=""):
    """Print a formatted separator."""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("=" * 80)

def format_response(result):
    """Format the orchestrator response for better readability."""
    print("🎉 SUCCESS! Orchestrator Response:")
    print_separator()
    
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
        if any(agent in response_text for agent in ['InfoAgent', 'PatientContextAgent', 'ActionAgent']):
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

def test_scenario(scenario_name, test_data):
    """Test a specific scenario."""
    print_separator(f"TESTING: {scenario_name}")
    
    url = "http://127.0.0.1:8000/api/orchestrator"
    
    print(f"📤 Message: {test_data['message']}")
    print()
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            format_response(result)
        else:
            print("❌ HTTP ERROR:")
            print("-" * 40)
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("Make sure the server is running on http://127.0.0.1:8000")

def main():
    """Run multiple test scenarios."""
    
    scenarios = [
        {
            "name": "Cardiology Appointment",
            "data": {
                "message": "Hi, I'm taking my mother to her cardiology appointment next week. What should I bring?",
                "session_id": "cardiology_test_001",
                "patient_context": {
                    "patient_id": "patient_001",
                    "appointment_type": "cardiology"
                }
            }
        },
        {
            "name": "General Doctor Visit",
            "data": {
                "message": "My father has a routine checkup with his primary care doctor tomorrow. What should we prepare?",
                "session_id": "general_test_002",
                "patient_context": {
                    "patient_id": "patient_002",
                    "appointment_type": "primary_care"
                }
            }
        },
        {
            "name": "Specialist Referral",
            "data": {
                "message": "We're seeing a neurologist for the first time. What documentation should we bring?",
                "session_id": "specialist_test_003",
                "patient_context": {
                    "patient_id": "patient_003",
                    "appointment_type": "neurology",
                    "is_first_visit": True
                }
            }
        }
    ]
    
    print("🏥 ORCHESTRATOR SERVICE TEST SUITE")
    print("Testing multiple healthcare appointment scenarios...")
    
    for scenario in scenarios:
        test_scenario(scenario["name"], scenario["data"])
        input("\n⏸️  Press Enter to continue to next test...")
    
    print("\n🎯 All tests completed!")

if __name__ == "__main__":
    main()