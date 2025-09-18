"""
Test script to compare Simple Orchestrator vs Semantic Kernel Orchestrator responses.
"""

import asyncio
import aiohttp
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_orchestrator(endpoint: str, message: str, orchestrator_name: str):
    """Test a specific orchestrator endpoint."""
    url = f"{BASE_URL}{endpoint}"
    payload = {
        "message": message,
        "session_id": f"test_session_{int(time.time())}"
    }
    
    logger.info(f"Testing {orchestrator_name} with message: {message[:50]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            async with session.post(url, json=payload) as response:
                end_time = time.time()
                
                if response.status == 200:
                    result = await response.json()
                    response_time = end_time - start_time
                    
                    print(f"\n{'='*60}")
                    print(f"{orchestrator_name.upper()} RESPONSE")
                    print(f"{'='*60}")
                    print(f"Response Time: {response_time:.2f} seconds")
                    print(f"Success: {result.get('success', False)}")
                    
                    if result.get('success'):
                        response_text = result.get('response', '')
                        print(f"\nResponse Text ({len(response_text)} chars):")
                        print("-" * 40)
                        print(response_text)
                        
                        # Show structured data if available
                        structured = result.get('structured_data', {})
                        if structured:
                            checklist = structured.get('checklist', [])
                            if checklist:
                                print(f"\nChecklist ({len(checklist)} items):")
                                for i, item in enumerate(checklist[:5], 1):  # Show first 5
                                    print(f"  {i}. {item}")
                                if len(checklist) > 5:
                                    print(f"  ... and {len(checklist) - 5} more items")
                            
                            follow_up = structured.get('follow_up_actions', [])
                            if follow_up:
                                print(f"\nFollow-up Actions ({len(follow_up)} items):")
                                for action in follow_up:
                                    print(f"  • {action}")
                        
                        # Show orchestrator type if available
                        orchestrator_type = result.get('orchestrator_type', 'unknown')
                        print(f"\nOrchestrator Type: {orchestrator_type}")
                    else:
                        error = result.get('error', 'Unknown error')
                        print(f"Error: {error}")
                        
                else:
                    print(f"\n{orchestrator_name} FAILED: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"\n{orchestrator_name} EXCEPTION: {e}")


async def run_comparison_test():
    """Run comparison test between both orchestrators."""
    test_messages = [
        "Hi, I am taking my mother to her cardiology appointment next week. What should I bring?",
        "My mom has atrial fibrillation and takes blood thinners. What questions should I ask the cardiologist?",
        "What documents do I need for a follow-up heart appointment?",
        "Help me prepare for my mother's first cardiology visit. She's 72 and has high blood pressure."
    ]
    
    print("=" * 80)
    print("ORCHESTRATOR COMPARISON TEST")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Test Messages: {len(test_messages)}")
    print("=" * 80)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n\n🔥 TEST {i}/{len(test_messages)}")
        print(f"Message: {message}")
        print("=" * 80)
        
        # Test both orchestrators
        await test_orchestrator("/api/orchestrator", message, "Simple Orchestrator")
        await test_orchestrator("/api/orchestrator/semantic-kernel", message, "Semantic Kernel Orchestrator")
        
        if i < len(test_messages):
            print("\n" + "⏱️ " * 20 + " WAITING 2 SECONDS " + "⏱️ " * 20)
            await asyncio.sleep(2)  # Brief pause between tests
    
    print("\n" + "=" * 80)
    print("✅ COMPARISON TEST COMPLETED")
    print("=" * 80)


async def main():
    """Main test function."""
    try:
        await run_comparison_test()
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test failed with exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())