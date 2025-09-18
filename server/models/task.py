from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Task(BaseModel):
    """Task model for forward-compatible task tracking (minimal MVP implementation)."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique task identifier")
    session_id: str = Field(..., description="Session this task belongs to")
    originating_agent: str = Field(..., description="Agent that created this task")
    status: str = Field(default="queued", description="Task status: queued, running, succeeded, failed, canceled")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    result_summary: Optional[str] = Field(default=None, max_length=2048, description="Summary of task results")
    error_code: Optional[str] = Field(default=None, max_length=128, description="Error code if task failed")
    progress: int = Field(default=0, ge=0, le=100, description="Task progress percentage")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_status(self, new_status: str, summary: Optional[str] = None, error_code: Optional[str] = None) -> None:
        """Update task status and related fields."""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if summary:
            self.result_summary = summary
        if error_code:
            self.error_code = error_code
        
        # Update progress based on status
        if new_status == "succeeded":
            self.progress = 100
        elif new_status == "failed" or new_status == "canceled":
            # Keep current progress for failed/canceled tasks
            pass
        elif new_status == "running":
            # Don't auto-update progress for running tasks
            pass
    
    def is_complete(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in ["succeeded", "failed", "canceled"]
    
    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.status == "running"
    
    def duration(self) -> float:
        """Get task duration in seconds."""
        return (self.updated_at - self.created_at).total_seconds()


class ToolInvocation(BaseModel):
    """Tool invocation model for logging function/tool calls."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique invocation identifier")
    task_id: Optional[str] = Field(default=None, description="Associated task ID if applicable")
    tool_name: str = Field(..., description="Name of the tool being invoked")
    parameters: dict = Field(default_factory=dict, description="Sanitized parameters for the tool call")
    outcome_status: str = Field(default="pending", description="Outcome status: pending, success, error")
    duration: Optional[float] = Field(default=None, description="Execution duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Invocation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def mark_success(self, duration: float) -> None:
        """Mark invocation as successful."""
        self.outcome_status = "success"
        self.duration = duration
    
    def mark_error(self, duration: float) -> None:
        """Mark invocation as failed."""
        self.outcome_status = "error"
        self.duration = duration
    
    def is_complete(self) -> bool:
        """Check if invocation is complete."""
        return self.outcome_status in ["success", "error"]