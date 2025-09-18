"""
Test script to verify that the ACS Media Handler is now using Semantic Kernel orchestrator.
"""

import asyncio
import logging
from app.handler.acs_media_handler import ACSMediaHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_semantic_kernel_voice_integration():
    """Test that the media handler is using Semantic Kernel orchestrator."""
    
    # Mock config similar to what server.py uses
    config = {
        "AZURE_VOICE_LIVE_API_KEY": os.getenv("AZURE_VOICE_LIVE_API_KEY", ""),
        "AZURE_VOICE_LIVE_ENDPOINT": os.getenv("AZURE_VOICE_LIVE_ENDPOINT"),
        "VOICE_LIVE_MODEL": os.getenv("VOICE_LIVE_MODEL", "gpt-4o-mini"),
        "ACS_CONNECTION_STRING": os.getenv("ACS_CONNECTION_STRING"),
        "ACS_DEV_TUNNEL": os.getenv("ACS_DEV_TUNNEL", ""),
        "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID": os.getenv("AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID", "")
    }
    
    print("🔥 Testing Semantic Kernel Voice Integration")
    print("=" * 50)
    
    try:
        # Create media handler
        handler = ACSMediaHandler(config)
        
        print(f"✅ ACS Media Handler created successfully")
        print(f"📝 Endpoint: {handler.endpoint}")
        print(f"🤖 Model: {handler.model}")
        print(f"🎯 Use Orchestrator: {handler.use_orchestrator}")
        
        # Test orchestrator initialization
        print("\n🚀 Testing Semantic Kernel Orchestrator Initialization...")
        success = await handler.initialize_orchestrator()
        
        if success:
            print("✅ Semantic Kernel Orchestrator initialized successfully!")
            print(f"🔧 Orchestrator Service: {type(handler.orchestrator_service).__name__}")
            print(f"📊 Orchestrator Available: {handler.orchestrator_service is not None}")
            
            if hasattr(handler.orchestrator_service, 'deployment_name'):
                print(f"🎯 Deployment: {handler.orchestrator_service.deployment_name}")
            if hasattr(handler.orchestrator_service, '_initialized'):
                print(f"🔄 Initialized: {handler.orchestrator_service._initialized}")
        else:
            print("❌ Failed to initialize Semantic Kernel Orchestrator")
            
    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_semantic_kernel_voice_integration())