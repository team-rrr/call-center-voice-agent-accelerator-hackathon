import pytest
import pytest_asyncio
import json
import uuid
from datetime import datetime
from quart import Quart, websocket


class MockErrorEventService:
    """Mock error event service for testing."""
    
    def __init__(self):
        self.events = []
    
    async def emit_error(self, error_type: str, message: str, details=None):
        """Emit an error event."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "details": details
        }
        self.events.append(event)
        return event
    
    def get_events(self):
        """Get all emitted events."""
        return self.events
    
    def clear_events(self):
        """Clear all events."""
        self.events = []


@pytest.fixture
def error_service():
    """Provide a mock error event service."""
    return MockErrorEventService()


@pytest_asyncio.fixture
async def error_handling_app(error_service):
    """Create a test app that simulates error scenarios."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        session_id = str(uuid.uuid4())
        
        try:
            await websocket.send(json.dumps({
                "event": "session_started",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for client message to determine test scenario
            client_message = await websocket.receive()
            test_scenario = json.loads(client_message)
            
            if test_scenario.get("trigger") == "transcription_error":
                # Simulate transcription failure
                error_event = await error_service.emit_error(
                    "transcription_error",
                    "Failed to transcribe audio stream",
                    {"confidence": 0.1, "error_code": "AUDIO_QUALITY_LOW"}
                )
                
                await websocket.send(json.dumps({
                    "event": "error",
                    "session_id": session_id,
                    "error": error_event,
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif test_scenario.get("trigger") == "llm_error":
                # Simulate LLM API failure
                error_event = await error_service.emit_error(
                    "llm_api_error", 
                    "External LLM API call failed",
                    {"status_code": 500, "endpoint": "https://api.openai.com", "retry_count": 2}
                )
                
                await websocket.send(json.dumps({
                    "event": "error",
                    "session_id": session_id,
                    "error": error_event,
                    "timestamp": datetime.now().isoformat()
                }))
                
            elif test_scenario.get("trigger") == "tts_error":
                # Simulate TTS failure
                error_event = await error_service.emit_error(
                    "tts_error",
                    "Text-to-speech synthesis failed",
                    {"voice": "en-US-JennyNeural", "text_length": 150}
                )
                
                await websocket.send(json.dumps({
                    "event": "error",
                    "session_id": session_id,
                    "error": error_event,
                    "timestamp": datetime.now().isoformat()
                }))
                
            else:
                # Normal flow
                await websocket.send(json.dumps({
                    "event": "session_ended",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }))
                
        except Exception as e:
            # Handle unexpected errors
            error_event = await error_service.emit_error(
                "internal_error",
                f"Unexpected error in WebSocket handler: {str(e)}",
                {"exception_type": type(e).__name__}
            )
            
            await websocket.send(json.dumps({
                "event": "error",
                "session_id": session_id,
                "error": error_event,
                "timestamp": datetime.now().isoformat()
            }))
    
    return app


@pytest.mark.asyncio
async def test_transcription_error_event(error_handling_app, error_service):
    """Test error event emission for transcription failures."""
    async with error_handling_app.test_client() as client:
        async with client.websocket("/ws") as ws:
            # Receive session started
            session_started = json.loads(await ws.receive())
            assert session_started["event"] == "session_started"
            
            # Trigger transcription error
            await ws.send(json.dumps({"trigger": "transcription_error"}))
            
            # Receive error event
            error_message = json.loads(await ws.receive())
            assert error_message["event"] == "error"
            
            error_event = error_message["error"]
            assert error_event["error_type"] == "transcription_error"
            assert "Failed to transcribe" in error_event["message"]
            assert error_event["details"]["confidence"] == 0.1
            
            # Verify error was logged in service
            events = error_service.get_events()
            assert len(events) == 1
            assert events[0]["error_type"] == "transcription_error"


@pytest.mark.asyncio
async def test_llm_api_error_event(error_handling_app, error_service):
    """Test error event emission for LLM API failures."""
    async with error_handling_app.test_client() as client:
        async with client.websocket("/ws") as ws:
            # Skip to error trigger
            await ws.receive()  # session_started
            await ws.send(json.dumps({"trigger": "llm_error"}))
            
            error_message = json.loads(await ws.receive())
            assert error_message["event"] == "error"
            
            error_event = error_message["error"]
            assert error_event["error_type"] == "llm_api_error"
            assert "External LLM API" in error_event["message"]
            assert error_event["details"]["status_code"] == 500
            assert error_event["details"]["retry_count"] == 2


@pytest.mark.asyncio
async def test_tts_error_event(error_handling_app, error_service):
    """Test error event emission for TTS failures.""" 
    async with error_handling_app.test_client() as client:
        async with client.websocket("/ws") as ws:
            await ws.receive()  # session_started
            await ws.send(json.dumps({"trigger": "tts_error"}))
            
            error_message = json.loads(await ws.receive())
            assert error_message["event"] == "error"
            
            error_event = error_message["error"]
            assert error_event["error_type"] == "tts_error"
            assert "Text-to-speech" in error_event["message"]
            assert error_event["details"]["voice"] == "en-US-JennyNeural"


def test_error_event_service_functionality(error_service):
    """Test the error event service directly."""
    # Test error emission
    import asyncio
    
    async def test_async():
        error_event = await error_service.emit_error(
            "test_error",
            "This is a test error",
            {"test_data": "value"}
        )
        
        assert error_event["error_type"] == "test_error"
        assert error_event["message"] == "This is a test error"
        assert error_event["details"]["test_data"] == "value"
        assert "id" in error_event
        assert "timestamp" in error_event
        
        # Verify UUID format
        uuid.UUID(error_event["id"])
        
        # Verify it was stored
        events = error_service.get_events()
        assert len(events) == 1
        assert events[0] == error_event
    
    asyncio.run(test_async())


def test_error_service_multiple_events(error_service):
    """Test handling multiple error events."""
    import asyncio
    
    async def test_async():
        # Emit multiple errors
        await error_service.emit_error("error1", "First error")
        await error_service.emit_error("error2", "Second error") 
        await error_service.emit_error("error3", "Third error")
        
        events = error_service.get_events()
        assert len(events) == 3
        
        error_types = [e["error_type"] for e in events]
        assert error_types == ["error1", "error2", "error3"]
        
        # Test clearing
        error_service.clear_events()
        assert len(error_service.get_events()) == 0
    
    asyncio.run(test_async())


@pytest.mark.asyncio
async def test_error_event_structure_validation():
    """Test that error events conform to expected structure."""
    error_service = MockErrorEventService()
    
    error_event = await error_service.emit_error(
        "validation_test",
        "Testing error structure",
        {"key": "value", "number": 42}
    )
    
    # Required fields
    required_fields = ["id", "timestamp", "error_type", "message"]
    for field in required_fields:
        assert field in error_event
    
    # Optional details field
    assert "details" in error_event
    assert isinstance(error_event["details"], dict)
    
    # Validate types
    assert isinstance(error_event["id"], str)
    assert isinstance(error_event["timestamp"], str)
    assert isinstance(error_event["error_type"], str)
    assert isinstance(error_event["message"], str)
    
    # Validate UUID format
    uuid.UUID(error_event["id"])
    
    # Validate timestamp format (contains T for ISO format)
    assert "T" in error_event["timestamp"]


@pytest.mark.asyncio
async def test_error_recovery_scenarios():
    """Test different error recovery scenarios."""
    error_service = MockErrorEventService()
    
    # Test transient error (should be retryable)
    transient_error = await error_service.emit_error(
        "network_timeout",
        "Request timed out",
        {"retryable": True, "retry_after": 5}
    )
    
    assert transient_error["details"]["retryable"] is True
    
    # Test permanent error (should not be retryable)
    permanent_error = await error_service.emit_error(
        "authentication_failed",
        "Invalid API key",
        {"retryable": False, "action_required": "update_credentials"}
    )
    
    assert permanent_error["details"]["retryable"] is False
    
    events = error_service.get_events()
    assert len(events) == 2