from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

from ..models.task import Task


logger = logging.getLogger(__name__)


class ErrorEventService:
    """
    Service for emitting and managing structured error events.
    Provides consistent error handling and logging across the application.
    """
    
    def __init__(self):
        """Initialize error event service."""
        self._events: List[Dict[str, Any]] = []
        self._max_events = 1000  # Keep last 1000 events in memory
    
    async def emit_error(
        self, 
        error_type: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emit a structured error event.
        
        Args:
            error_type: Type/category of error
            message: Human-readable error message
            details: Optional additional error details
            session_id: Optional session ID where error occurred
            
        Returns:
            Error event dictionary
        """
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "session_id": session_id
        }
        
        # Add to events list
        self._events.append(event)
        
        # Trim events if too many
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
        
        # Log the error event
        log_level = self._get_log_level(error_type)
        logger.log(log_level, f"Error event [{error_type}]: {message}")
        
        if details:
            logger.debug(f"Error details: {details}")
        
        return event
    
    async def emit_transcription_error(
        self, 
        message: str, 
        session_id: str, 
        confidence: Optional[float] = None,
        audio_length: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Emit a transcription-specific error.
        
        Args:
            message: Error message
            session_id: Session where error occurred
            confidence: Transcription confidence if available
            audio_length: Audio length in seconds if available
            
        Returns:
            Error event dictionary
        """
        details = {"source": "transcription_service"}
        
        if confidence is not None:
            details["confidence"] = confidence
        if audio_length is not None:
            details["audio_length_seconds"] = audio_length
        
        return await self.emit_error(
            "transcription_error",
            message,
            details,
            session_id
        )
    
    async def emit_tts_error(
        self, 
        message: str, 
        session_id: str, 
        text_length: Optional[int] = None,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emit a text-to-speech error.
        
        Args:
            message: Error message
            session_id: Session where error occurred
            text_length: Length of text being synthesized
            voice: Voice being used
            
        Returns:
            Error event dictionary
        """
        details = {"source": "tts_service"}
        
        if text_length is not None:
            details["text_length"] = text_length
        if voice:
            details["voice"] = voice
        
        return await self.emit_error(
            "tts_error",
            message,
            details,
            session_id
        )
    
    async def emit_llm_error(
        self, 
        message: str, 
        session_id: str, 
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        status_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Emit an LLM API error.
        
        Args:
            message: Error message
            session_id: Session where error occurred
            model: LLM model being used
            tokens_used: Tokens used in request
            status_code: HTTP status code if applicable
            
        Returns:
            Error event dictionary
        """
        details = {"source": "llm_service"}
        
        if model:
            details["model"] = model
        if tokens_used is not None:
            details["tokens_used"] = tokens_used
        if status_code:
            details["status_code"] = status_code
        
        return await self.emit_error(
            "llm_api_error",
            message,
            details,
            session_id
        )
    
    async def emit_websocket_error(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emit a WebSocket connection error.
        
        Args:
            message: Error message
            session_id: Session where error occurred
            connection_id: WebSocket connection ID
            error_code: WebSocket error code
            
        Returns:
            Error event dictionary
        """
        details = {"source": "websocket_handler"}
        
        if connection_id:
            details["connection_id"] = connection_id
        if error_code:
            details["error_code"] = error_code
        
        return await self.emit_error(
            "websocket_error",
            message,
            details,
            session_id
        )
    
    async def emit_session_error(
        self, 
        message: str, 
        session_id: str,
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Emit a session management error.
        
        Args:
            message: Error message
            session_id: Session where error occurred
            operation: Operation that failed
            
        Returns:
            Error event dictionary
        """
        details = {"source": "session_management"}
        
        if operation:
            details["operation"] = operation
        
        return await self.emit_error(
            "session_error",
            message,
            details,
            session_id
        )
    
    def get_recent_events(self, limit: int = 50, error_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent error events.
        
        Args:
            limit: Maximum number of events to return
            error_type: Optional filter by error type
            
        Returns:
            List of error events (most recent first)
        """
        events = self._events.copy()
        
        if error_type:
            events = [e for e in events if e["error_type"] == error_type]
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return events[:limit]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        if not self._events:
            return {
                "total_errors": 0,
                "error_types": {},
                "recent_error_rate": 0.0,
                "last_error": None
            }
        
        # Count errors by type
        error_types = {}
        for event in self._events:
            error_type = event["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Calculate recent error rate (last hour)
        from datetime import timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e for e in self._events 
            if datetime.fromisoformat(e["timestamp"]) > one_hour_ago
        ]
        
        return {
            "total_errors": len(self._events),
            "error_types": error_types,
            "recent_error_rate": len(recent_errors),  # Errors per hour
            "last_error": self._events[-1] if self._events else None
        }
    
    def clear_events(self) -> None:
        """Clear all stored error events."""
        self._events.clear()
        logger.info("Cleared all error events")
    
    def _get_log_level(self, error_type: str) -> int:
        """
        Get appropriate log level for error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Logging level constant
        """
        # Map error types to log levels
        error_levels = {
            "transcription_error": logging.WARNING,
            "tts_error": logging.WARNING,
            "llm_api_error": logging.ERROR,
            "websocket_error": logging.ERROR,
            "session_error": logging.ERROR,
            "internal_error": logging.CRITICAL,
            "security_error": logging.CRITICAL
        }
        
        return error_levels.get(error_type, logging.ERROR)