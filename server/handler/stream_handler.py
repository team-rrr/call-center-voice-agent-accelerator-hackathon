import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from quart import websocket
from models.session import Session
from models.utterance import Utterance
from models.agent import AgentMessage
from services.session_store import SessionStore
from services.agent_runtime import AgentRuntime
from services.transcription import TranscriptionService
from services.tts import TTSService
from services.error_events import ErrorEventService
from services.redaction import comprehensive_redaction


logger = logging.getLogger(__name__)


class StreamHandler:
    """
    WebSocket stream handler for real-time voice interactions.
    Manages the full flow from audio input to agent responses.
    """
    
    def __init__(
        self, 
        session_store: SessionStore,
        agent_runtime: AgentRuntime,
        transcription_service: TranscriptionService,
        tts_service: TTSService,
        error_service: ErrorEventService
    ):
        """
        Initialize stream handler.
        
        Args:
            session_store: Session management service
            agent_runtime: Agent runtime service
            transcription_service: Transcription service
            tts_service: Text-to-speech service
            error_service: Error event service
        """
        self.session_store = session_store
        self.agent_runtime = agent_runtime
        self.transcription_service = transcription_service
        self.tts_service = tts_service
        self.error_service = error_service
        
        self._active_connections: Dict[str, Dict[str, Any]] = {}
    
    async def handle_websocket_connection(self) -> None:
        """
        Handle a new WebSocket connection for voice streaming.
        This is the main entry point for WebSocket connections.
        """
        connection_id = str(uuid.uuid4())
        session_id = None
        
        try:
            # Register connection
            self._active_connections[connection_id] = {
                "session_id": None,
                "connected_at": datetime.now(),
                "last_activity": datetime.now()
            }
            
            logger.info(f"New WebSocket connection: {connection_id}")
            
            # Start session
            session = await self.session_store.create_session()
            session_id = session.id
            
            self._active_connections[connection_id]["session_id"] = session_id
            
            # Send session started event
            await self._send_event("session_started", {
                "session_id": session_id,
                "connection_id": connection_id
            })
            
            # Handle messages
            await self._handle_connection_messages(connection_id, session_id)
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            
            if session_id:
                await self.error_service.emit_websocket_error(
                    f"Connection error: {str(e)}",
                    session_id,
                    connection_id
                )
            
        finally:
            # Clean up connection
            await self._cleanup_connection(connection_id, session_id)
    
    async def _handle_connection_messages(self, connection_id: str, session_id: str) -> None:
        """
        Handle incoming WebSocket messages for a connection.
        
        Args:
            connection_id: WebSocket connection identifier
            session_id: Associated session identifier
        """
        try:
            async for message in websocket:
                await self._update_activity(connection_id)
                
                try:
                    data = json.loads(message)
                    await self._process_message(connection_id, session_id, data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from {connection_id}")
                    await self._send_error("invalid_json", "Invalid JSON format")
                    
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await self.error_service.emit_websocket_error(
                        f"Message processing error: {str(e)}",
                        session_id,
                        connection_id
                    )
                    await self._send_error("processing_error", str(e))
                    
        except Exception as e:
            logger.error(f"Connection message handling error: {str(e)}")
    
    async def _process_message(self, connection_id: str, session_id: str, data: Dict[str, Any]) -> None:
        """
        Process a WebSocket message.
        
        Args:
            connection_id: WebSocket connection identifier
            session_id: Session identifier
            data: Message data
        """
        message_type = data.get("type", "unknown")
        
        if message_type == "transcript_partial":
            await self._handle_partial_transcript(session_id, data)
            
        elif message_type == "transcript_final":
            await self._handle_final_transcript(session_id, data)
            
        elif message_type == "user_interrupt":
            await self._handle_user_interrupt(session_id, data)
            
        elif message_type == "end_session":
            await self._handle_end_session(session_id)
            
        elif message_type == "ping":
            await self._send_event("pong", {"timestamp": datetime.now().isoformat()})
            
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await self._send_error("unknown_message_type", f"Unknown message type: {message_type}")
    
    async def _handle_partial_transcript(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Handle partial transcript data.
        
        Args:
            session_id: Session identifier
            data: Transcript data
        """
        try:
            text = data.get("text", "")
            confidence = data.get("confidence", 0.5)
            
            if not text:
                return
            
            # Create partial utterance
            utterance = await self.transcription_service.process_partial_transcript(
                text, session_id, confidence
            )
            
            if utterance:
                # Send partial transcript event
                await self._send_event("transcript_partial", {
                    "session_id": session_id,
                    "text": text,
                    "confidence": confidence,
                    "utterance_id": utterance.id
                })
                
        except Exception as e:
            logger.error(f"Error handling partial transcript: {str(e)}")
            await self.error_service.emit_transcription_error(
                f"Partial transcript error: {str(e)}",
                session_id
            )
    
    async def _handle_final_transcript(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Handle final transcript data and process with agent.
        
        Args:
            session_id: Session identifier
            data: Transcript data
        """
        try:
            text = data.get("text", "")
            confidence = data.get("confidence", 0.8)
            interrupted = data.get("interrupted", False)
            
            if not text:
                return
            
            # Create final utterance
            utterance = Utterance(
                session_id=session_id,
                text=text,
                confidence=confidence,
                interrupted=interrupted
            )
            
            # Apply redaction to utterance text for transcript
            redacted_text = comprehensive_redaction(text)
            
            # Send final transcript event (with redacted text)
            await self._send_event("transcript_final", {
                "session_id": session_id,
                "text": redacted_text,
                "confidence": confidence,
                "interrupted": interrupted,
                "utterance_id": utterance.id
            })
            
            # Process with agent (use original text for processing)
            if not interrupted:
                agent_response = await self.agent_runtime.process_utterance(utterance)
                
                if agent_response:
                    await self._handle_agent_response(session_id, agent_response)
            
        except Exception as e:
            logger.error(f"Error handling final transcript: {str(e)}")
            await self.error_service.emit_transcription_error(
                f"Final transcript error: {str(e)}",
                session_id
            )
    
    async def _handle_agent_response(self, session_id: str, agent_response: AgentMessage) -> None:
        """
        Handle agent response and convert to speech.
        
        Args:
            session_id: Session identifier
            agent_response: Agent response message
        """
        try:
            response_text = agent_response.payload.get("response_text", "") if agent_response.payload else ""
            
            if not response_text:
                logger.warning(f"Empty agent response for session {session_id}")
                return
            
            # Send agent response event
            await self._send_event("agent_response", {
                "session_id": session_id,
                "agent": agent_response.agent,
                "text": response_text,
                "message_id": agent_response.id
            })
            
            # Synthesize and play speech
            try:
                playback_id = await self.tts_service.synthesize_and_play(
                    response_text, session_id, agent_response.agent
                )
                
                if playback_id:
                    await self._send_event("agent_response_started", {
                        "session_id": session_id,
                        "playback_id": playback_id,
                        "text": response_text
                    })
                    
                    # Note: In a real implementation, we'd wait for playback completion
                    # For MVP, we just simulate it
                    await asyncio.sleep(len(response_text) * 0.1)  # Rough timing
                    
                    await self._send_event("agent_response_completed", {
                        "session_id": session_id,
                        "playback_id": playback_id
                    })
                    
            except Exception as e:
                await self.error_service.emit_tts_error(
                    f"TTS error: {str(e)}",
                    session_id,
                    len(response_text)
                )
                
        except Exception as e:
            logger.error(f"Error handling agent response: {str(e)}")
            await self.error_service.emit_llm_error(
                f"Agent response error: {str(e)}",
                session_id
            )
    
    async def _handle_user_interrupt(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Handle user interruption (barge-in).
        
        Args:
            session_id: Session identifier
            data: Interruption data
        """
        try:
            # Stop current TTS playback
            playback_stopped = await self.tts_service.handle_barge_in(session_id)
            
            if playback_stopped:
                await self._send_event("playback_stopped", {
                    "session_id": session_id,
                    "reason": "user_interrupt"
                })
            
            # Handle interruption with agent
            agent_response = await self.agent_runtime.handle_interruption(session_id)
            
            if agent_response:
                await self._handle_agent_response(session_id, agent_response)
                
        except Exception as e:
            logger.error(f"Error handling user interrupt: {str(e)}")
            await self.error_service.emit_session_error(
                f"Interrupt handling error: {str(e)}",
                session_id,
                "handle_interrupt"
            )
    
    async def _handle_end_session(self, session_id: str) -> None:
        """
        Handle session end request.
        
        Args:
            session_id: Session identifier
        """
        try:
            # End session in store
            session = await self.session_store.end_session(session_id)
            
            if session:
                # Clean up agent context
                self.agent_runtime.remove_session_context(session_id)
                
                # Send session ended event
                await self._send_event("session_ended", {
                    "session_id": session_id,
                    "duration": session.duration()
                })
                
                logger.info(f"Session {session_id} ended")
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            await self.error_service.emit_session_error(
                f"Session end error: {str(e)}",
                session_id,
                "end_session"
            )
    
    async def _send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Send an event to the WebSocket client.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            event = {
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            await websocket.send(json.dumps(event))
            
        except Exception as e:
            logger.error(f"Error sending event {event_type}: {str(e)}")
    
    async def _send_error(self, error_type: str, message: str) -> None:
        """
        Send an error event to the WebSocket client.
        
        Args:
            error_type: Type of error
            message: Error message
        """
        await self._send_event("error", {
            "error_type": error_type,
            "message": message
        })
    
    async def _update_activity(self, connection_id: str) -> None:
        """
        Update last activity time for a connection.
        
        Args:
            connection_id: Connection identifier
        """
        if connection_id in self._active_connections:
            self._active_connections[connection_id]["last_activity"] = datetime.now()
    
    async def _cleanup_connection(self, connection_id: str, session_id: Optional[str]) -> None:
        """
        Clean up connection and associated resources.
        
        Args:
            connection_id: Connection identifier
            session_id: Session identifier (if any)
        """
        try:
            # Remove connection
            if connection_id in self._active_connections:
                del self._active_connections[connection_id]
            
            # End session if active
            if session_id:
                await self._handle_end_session(session_id)
            
            logger.info(f"Cleaned up connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up connection: {str(e)}")
    
    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about active connections.
        
        Returns:
            Dictionary of active connection information
        """
        return self._active_connections.copy()