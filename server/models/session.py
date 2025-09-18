from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Session(BaseModel):
    """Session model representing a voice interaction session."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    status: str = Field(..., description="Session status: active or ended")
    start_time: datetime = Field(default_factory=datetime.now, description="Session start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Session end timestamp")
    version: str = Field(default="1.0.0", description="Session version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def end_session(self) -> None:
        """Mark the session as ended."""
        self.status = "ended"
        self.end_time = datetime.now()
    
    def is_active(self) -> bool:
        """Check if the session is active."""
        return self.status == "active"
    
    def duration(self) -> Optional[float]:
        """Get session duration in seconds if ended."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None