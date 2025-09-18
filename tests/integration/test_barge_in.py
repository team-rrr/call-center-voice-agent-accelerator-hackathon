import pytest
import pytest_asyncio
import asyncio
import json
import uuid
from datetime import datetime
from quart import Quart, websocket


@pytest_asyncio.fixture
async def barge_in_app():
    """Create a test Quart app that simulates barge-in behavior."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        session_id = str(uuid.uuid4())
        
        # Start session
        await websocket.send(json.dumps({
            "event": "session_started",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Start agent response (simulating TTS playback)
        await websocket.send(json.dumps({
            "event": "agent_response_started",
            "session_id": session_id,
            "text": "I am speaking a long response that can be interrupted...",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and wait for messages
        try:
            while True:
                interrupt_data = await asyncio.wait_for(websocket.receive(), timeout=0.5)
                interrupt_event = json.loads(interrupt_data)
                
                if interrupt_event.get("event") == "user_interrupt":
                    # Send playback stopped event
                    await websocket.send(json.dumps({
                        "event": "playback_stopped",
                        "session_id": session_id,
                        "reason": "user_interrupt",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Process new user input
                    await websocket.send(json.dumps({
                        "event": "transcript_final",
                        "session_id": session_id,
                        "text": interrupt_event.get("text", "Sorry, can you repeat that?"),
                        "confidence": 0.9,
                        "interrupted": True,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    # Send new agent response
                    await websocket.send(json.dumps({
                        "event": "agent_response",
                        "session_id": session_id,
                        "text": "Of course! Let me help with that instead.",
                        "agent": "assistant",
                        "timestamp": datetime.now().isoformat()
                    }))
                    # Continue the loop to keep connection alive
        except asyncio.TimeoutError:
            # No interruption, complete original response
            await websocket.send(json.dumps({
                "event": "agent_response_completed",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Keep connection alive until client disconnects
        try:
            while True:
                await websocket.receive()
        except Exception:
            pass
    
    return app


@pytest.mark.asyncio
async def test_barge_in_interruption(barge_in_app):
    """Test that user can interrupt agent playback (barge-in)."""
    async with barge_in_app.test_client() as client:
        async with client.websocket("/ws") as ws:
            events = []
            
            # Receive initial events
            session_started = json.loads(await ws.receive())
            events.append(session_started)
            assert session_started["event"] == "session_started"
            
            response_started = json.loads(await ws.receive())
            events.append(response_started)
            assert response_started["event"] == "agent_response_started"
            
            # Simulate user interruption
            interrupt_signal = {
                "event": "user_interrupt",
                "text": "Sorry, can you repeat that?",
                "timestamp": datetime.now().isoformat()
            }
            await ws.send(json.dumps(interrupt_signal))
            
            # Collect remaining events
            try:
                while True:
                    data = await asyncio.wait_for(ws.receive(), timeout=1.0)
                    event = json.loads(data)
                    events.append(event)
            except asyncio.TimeoutError:
                pass
            
            # Verify interruption handling
            playback_stopped = next(e for e in events if e.get("event") == "playback_stopped")
            assert playback_stopped["reason"] == "user_interrupt"
            
            # Verify new transcript with interrupted flag
            new_transcript = next(e for e in events if e.get("event") == "transcript_final")
            assert new_transcript["interrupted"] is True
            assert new_transcript["text"] == "Sorry, can you repeat that?"
            
            # Verify new agent response
            new_response = next(e for e in events if e.get("event") == "agent_response")
            assert "instead" in new_response["text"].lower()


@pytest.mark.asyncio
async def test_no_interruption_flow():
    """Test normal flow when no interruption occurs."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        session_id = str(uuid.uuid4())
        
        await websocket.send(json.dumps({
            "event": "agent_response_started",
            "session_id": session_id,
            "text": "This is a normal response.",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Wait briefly for potential interruption
        try:
            await asyncio.wait_for(websocket.receive(), timeout=0.2)
        except asyncio.TimeoutError:
            # No interruption, complete normally
            await websocket.send(json.dumps({
                "event": "agent_response_completed",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
    
    async with app.test_client() as client:
        async with client.websocket("/ws") as ws:
            # Receive events without sending interruption
            response_started = json.loads(await ws.receive())
            assert response_started["event"] == "agent_response_started"
            
            response_completed = json.loads(await ws.receive())
            assert response_completed["event"] == "agent_response_completed"


@pytest.mark.asyncio
async def test_barge_in_timing():
    """Test that barge-in can happen at different times during playback."""
    app = Quart(__name__)
    
    @app.websocket("/ws")
    async def handle_websocket():
        session_id = str(uuid.uuid4())
        
        await websocket.send(json.dumps({
            "event": "agent_response_started", 
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Accept interruption at any time
        try:
            interrupt_data = await asyncio.wait_for(websocket.receive(), timeout=2.0)
            await websocket.send(json.dumps({
                "event": "playback_stopped",
                "session_id": session_id,
                "reason": "user_interrupt",
                "timestamp": datetime.now().isoformat()
            }))
        except asyncio.TimeoutError:
            pass
    
    async with app.test_client() as client:
        async with client.websocket("/ws") as ws:
            response_started = json.loads(await ws.receive())
            assert response_started["event"] == "agent_response_started"
            
            # Send immediate interruption
            await ws.send(json.dumps({
                "event": "user_interrupt",
                "timestamp": datetime.now().isoformat()
            }))
            
            playback_stopped = json.loads(await ws.receive())
            assert playback_stopped["event"] == "playback_stopped"
            assert playback_stopped["reason"] == "user_interrupt"