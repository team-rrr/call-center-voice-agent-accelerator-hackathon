import pytest
import pytest_asyncio
import asyncio
import json
import uuid
from datetime import datetime
from quart import Quart, websocket


@pytest_asyncio.fixture
async def websocket_app():
    """Create a test Quart app with WebSocket endpoint."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        # Send session_started event
        session_id = str(uuid.uuid4())
        await websocket.send(json.dumps({
            "event": "session_started",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Simulate receiving and processing partial transcript
        await websocket.send(json.dumps({
            "event": "transcript_partial",
            "session_id": session_id,
            "text": "Hello wor",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send final transcript
        await websocket.send(json.dumps({
            "event": "transcript_final",
            "session_id": session_id,
            "text": "Hello world",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send agent response
        await websocket.send(json.dumps({
            "event": "agent_response",
            "session_id": session_id,
            "text": "Hello! How can I help you today?",
            "agent": "assistant",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send session_ended event
        await websocket.send(json.dumps({
            "event": "session_ended",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive for the test
        try:
            while True:
                # Just wait for any message or disconnection
                await websocket.receive()
        except Exception:
            # Connection closed, that's expected
            pass
        
        # End session
        await websocket.send(json.dumps({
            "event": "session_ended",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Wait briefly for client to receive messages
        await asyncio.sleep(0.1)
    
    return app


@pytest.mark.asyncio
async def test_websocket_basic_flow(websocket_app):
    """Test the basic WebSocket flow for a voice session."""
    async with websocket_app.test_client() as client:
        async with client.websocket("/ws") as ws:
            events = []
            
            # Collect all events sent by the server
            try:
                while True:
                    data = await asyncio.wait_for(ws.receive(), timeout=1.0)
                    event = json.loads(data)
                    events.append(event)
            except asyncio.TimeoutError:
                pass  # Expected when no more messages
            
            # Verify we received all expected events in order
            assert len(events) == 5
            
            # Check session_started event
            assert events[0]["event"] == "session_started"
            assert "session_id" in events[0]
            session_id = events[0]["session_id"]
            
            # Check transcript_partial event
            assert events[1]["event"] == "transcript_partial"
            assert events[1]["session_id"] == session_id
            assert events[1]["text"] == "Hello wor"
            assert 0 <= events[1]["confidence"] <= 1
            
            # Check transcript_final event
            assert events[2]["event"] == "transcript_final"
            assert events[2]["session_id"] == session_id
            assert events[2]["text"] == "Hello world"
            assert 0 <= events[2]["confidence"] <= 1
            
            # Check agent_response event
            assert events[3]["event"] == "agent_response"
            assert events[3]["session_id"] == session_id
            assert events[3]["text"] == "Hello! How can I help you today?"
            assert events[3]["agent"] == "assistant"
            
            # Check session_ended event
            assert events[4]["event"] == "session_ended"
            assert events[4]["session_id"] == session_id


@pytest.mark.asyncio
async def test_websocket_event_format():
    """Test that WebSocket events have proper format and required fields."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        session_id = str(uuid.uuid4())
        await websocket.send(json.dumps({
            "event": "session_started",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
    
    async with app.test_client() as client:
        async with client.websocket("/ws") as ws:
            data = await ws.receive()
            event = json.loads(data)
            
            # Verify required fields
            assert "event" in event
            assert "session_id" in event
            assert "timestamp" in event
            
            # Verify session_id is valid UUID
            uuid.UUID(event["session_id"])
            
            # Verify timestamp format (basic check)
            assert "T" in event["timestamp"]  # ISO format contains T


@pytest.mark.asyncio  
async def test_websocket_connection_handling():
    """Test WebSocket connection establishment and teardown."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        # Simple echo to confirm connection
        await websocket.send(json.dumps({"status": "connected"}))
    
    async with app.test_client() as client:
        async with client.websocket("/ws") as ws:
            data = await ws.receive()
            response = json.loads(data)
            assert response["status"] == "connected"