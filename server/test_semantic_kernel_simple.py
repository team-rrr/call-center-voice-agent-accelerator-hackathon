"""
Simple test script for the new Semantic Kernel orchestrator endpoint.
"""

import asyncio
import aiohttp
import json

async def test_semantic_kernel_orchestrator():
    """Test the new Semantic Kernel orchestrator endpoint."""
    url = "http://localhost:8000/api/orchestrator/semantic-kernel"
    payload = {
        "message": "Hi, I am taking my mother to her cardiology appointment next week. What should I bring?",
        "session_id": "test_session_semantic_kernel"
    }
    
    print("Testing Semantic Kernel Orchestrator...")
    print(f"URL: {url}")
    print(f"Message: {payload['message']}")
    print("-" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ SUCCESS!")
                    print(f"Response: {result.get('response', 'No response text')}")
                    
                    if 'structured_data' in result:
                        structured = result['structured_data']
                        checklist = structured.get('checklist', [])
                        if checklist:
                            print(f"\nChecklist ({len(checklist)} items):")
                            for i, item in enumerate(checklist, 1):
                                print(f"  {i}. {item}")
                else:
                    print("❌ FAILED!")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")


if __name__ == "__main__":
    asyncio.run(test_semantic_kernel_orchestrator())