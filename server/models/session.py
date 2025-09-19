from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Session(BaseModel):
    """
    Session model representing a voice interaction session between a user and agent.
    
    A session encapsulates the entire conversation lifecycle from initial connection
    through final termination, tracking timing, status, and version information.
    
    Attributes:
        id: Unique UUID identifier for the session
        status: Current session status ("active" or "ended")
        start_time: When the session was initiated
        end_time: When the session ended (None if still active)
        version: Schema version for compatibility tracking
        
    Example:
        >>> session = Session(status="active")
        >>> session.is_active()
        True
        >>> session.end_session()
        >>> session.is_active()
        False
    """
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), 
        description="Unique session identifier (UUID4 format)"
    )
    status: str = Field(
        ..., 
        description="Session status: 'active' or 'ended'",
        regex="^(active|ended)$"
    )
    start_time: datetime = Field(
        default_factory=datetime.now, 
        description="Session start timestamp (ISO 8601 format)"
    )
    end_time: Optional[datetime] = Field(
        default=None, 
        description="Session end timestamp (ISO 8601 format, null if active)"
    )
    version: str = Field(
        default="1.0.0", 
        description="Session schema version (semantic versioning)"
    )
    
    class Config:
        """Pydantic configuration for Session model."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "active",
                "start_time": "2024-01-15T10:30:00Z",
                "end_time": None,
                "version": "1.0.0"
            }
        }
    
    def end_session(self) -> None:
        """
        Mark the session as ended and set the end timestamp.
        
        This method transitions the session from 'active' to 'ended' status
        and records the exact time of termination for duration calculation.
        
        Raises:
            ValueError: If session is already ended
        """
        if self.status == "ended":
            raise ValueError("Session is already ended")
            
        self.status = "ended"
        self.end_time = datetime.now()
    
    def is_active(self) -> bool:
        """
        Check if the session is currently active.
        
        Returns:
            bool: True if session status is 'active', False otherwise
        """
        return self.status == "active"
    
    def duration(self) -> Optional[float]:
        """
        Calculate session duration in seconds.
        
        For active sessions, returns None. For ended sessions, returns the
        total duration from start_time to end_time.
        
        Returns:
            Optional[float]: Duration in seconds if session is ended, None if active
        """
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None