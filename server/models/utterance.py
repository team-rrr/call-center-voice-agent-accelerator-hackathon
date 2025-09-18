from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Utterance(BaseModel):
    """Utterance model representing a segment of caller speech."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique utterance identifier")
    session_id: str = Field(..., description="Session this utterance belongs to")
    text: str = Field(..., min_length=1, description="Transcribed text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    start_time: datetime = Field(default_factory=datetime.now, description="Utterance start timestamp")
    end_time: datetime = Field(default_factory=datetime.now, description="Utterance end timestamp")
    interrupted: bool = Field(default=False, description="Whether utterance was interrupted")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def duration(self) -> float:
        """Get utterance duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if utterance has high confidence above threshold."""
        return self.confidence >= threshold
    
    def word_count(self) -> int:
        """Get word count of the utterance."""
        return len(self.text.split())
    
    def mark_interrupted(self) -> None:
        """Mark this utterance as interrupted."""
        self.interrupted = True