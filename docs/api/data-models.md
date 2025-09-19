# Data Models

This document describes the core data models used throughout the Voice Agent system.

## Overview

All models use Pydantic for validation and serialization. JSON Schema definitions are available in the `specs/001-what-a-voice/contracts/` directory.

## Core Models

### Session

Represents a voice interaction session between a user and agent.

```python
class Session(BaseModel):
    id: UUID = Field(..., description="Unique session identifier")
    status: SessionStatus = Field(..., description="Current session status")
    start_time: datetime = Field(..., description="Session start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Session end timestamp")
    version: str = Field(default="1.0.0", description="Session schema version")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
```

**SessionStatus Enum**:
- `active`: Session is currently active and accepting input
- `ended`: Session has been terminated

**Validation Rules**:
- Session with status `ended` must have `end_time` set
- `start_time` must be in the past
- `end_time` must be after `start_time` if present

**Example**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": null,
    "version": "1.0.0"
}
```

### Utterance

Represents a single spoken input from the user, transcribed to text.

```python
class Utterance(BaseModel):
    id: UUID = Field(..., description="Unique utterance identifier")
    session_id: UUID = Field(..., description="Associated session ID")
    text: str = Field(..., min_length=1, description="Transcribed text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Transcription confidence score")
    start_time: datetime = Field(..., description="Utterance start timestamp")
    end_time: datetime = Field(..., description="Utterance end timestamp")
    interrupted: bool = Field(default=False, description="Whether utterance was interrupted")
```

**Validation Rules**:
- `confidence` must be between 0.0 and 1.0
- `text` must not be empty
- `end_time` must be after `start_time`
- If `interrupted` is True, following agent audio was cut short

**Example**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Hello, I need help with my account",
    "confidence": 0.92,
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:30:03Z",
    "interrupted": false
}
```

### Agent

Represents an intelligent agent capable of handling user requests.

```python
class Agent(BaseModel):
    name: str = Field(..., description="Agent name/identifier")
    version: str = Field(default="1.0.0", description="Agent version")
    purpose: str = Field(..., description="Descriptive purpose of the agent")
    allowed_tools: List[str] = Field(default_factory=list, description="List of tools this agent can use")
    guardrails: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration object for guardrails")
```

**Methods**:
- `can_use_tool(tool_name: str) -> bool`: Check if agent can use a specific tool
- `add_tool(tool_name: str) -> None`: Add a tool to allowed tools list
- `remove_tool(tool_name: str) -> None`: Remove a tool from allowed tools list

**Example**:
```json
{
    "name": "customer_service_agent",
    "version": "1.0.0",
    "purpose": "Handle customer service inquiries and account operations",
    "allowed_tools": ["account_lookup", "balance_inquiry", "transaction_history"],
    "guardrails": {
        "max_tokens": 2000,
        "escalation_policy": "human_transfer_on_complex_issues"
    }
}
```

### Task

Represents a discrete unit of work performed by the agent.

```python
class Task(BaseModel):
    id: UUID = Field(..., description="Unique task identifier")
    session_id: UUID = Field(..., description="Associated session ID")
    description: str = Field(..., description="Human-readable task description")
    status: TaskStatus = Field(..., description="Current task status")
    agent_name: str = Field(..., description="Name of agent executing the task")
    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    result_summary: Optional[str] = Field(default=None, description="Summary of task execution result")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Task completion progress (0.0-1.0)")
```

**TaskStatus Enum**:
- `pending`: Task is queued for execution
- `in_progress`: Task is currently being executed
- `completed`: Task completed successfully
- `failed`: Task execution failed
- `cancelled`: Task was cancelled before completion

**Validation Rules**:
- `result_summary` only present if status is `completed`, `failed`, or `cancelled`
- `started_at` must be set when status is `in_progress` or later
- `completed_at` must be set when status is `completed`, `failed`, or `cancelled`

**Example**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "description": "Look up customer account information",
    "status": "completed",
    "agent_name": "customer_service_agent",
    "created_at": "2024-01-15T10:30:05Z",
    "started_at": "2024-01-15T10:30:06Z",
    "completed_at": "2024-01-15T10:30:08Z",
    "result_summary": "Account information retrieved successfully",
    "progress": 1.0
}
```

### ToolInvocation

Represents a specific tool call made during task execution.

```python
class ToolInvocation(BaseModel):
    id: UUID = Field(..., description="Unique invocation identifier")
    task_id: UUID = Field(..., description="Associated task ID")
    tool_name: str = Field(..., description="Name of the tool being invoked")
    parameters: Dict[str, Any] = Field(..., description="Tool invocation parameters")
    status: ToolInvocationStatus = Field(..., description="Invocation status")
    started_at: datetime = Field(..., description="Invocation start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Invocation completion timestamp")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool invocation result")
    error_message: Optional[str] = Field(default=None, description="Error message if invocation failed")
```

**ToolInvocationStatus Enum**:
- `pending`: Invocation is queued
- `running`: Invocation is executing
- `completed`: Invocation completed successfully
- `failed`: Invocation failed with error

**Example**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "task_id": "550e8400-e29b-41d4-a716-446655440002",
    "tool_name": "account_lookup",
    "parameters": {
        "customer_id": "CUST-12345",
        "include_balance": true
    },
    "status": "completed",
    "started_at": "2024-01-15T10:30:06Z",
    "completed_at": "2024-01-15T10:30:07Z",
    "result": {
        "account_status": "active",
        "balance": 1250.75,
        "last_transaction": "2024-01-14T15:22:00Z"
    },
    "error_message": null
}
```

## Event Models

### ErrorEvent

Represents an error that occurred during processing.

```python
class ErrorEvent(BaseModel):
    error_code: str = Field(..., description="Stable error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")
    session_id: Optional[UUID] = Field(default=None, description="Associated session ID if applicable")
    correlation_id: UUID = Field(..., description="Unique correlation ID for tracking")
    retry_possible: bool = Field(default=False, description="Whether the operation can be retried")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")
```

**Common Error Codes**:
- `TRANSCRIPTION_FAILED`: Audio transcription service error
- `TTS_FAILED`: Text-to-speech synthesis error
- `AGENT_RUNTIME_ERROR`: Agent execution error
- `TASK_EXECUTION_FAILED`: Task execution error
- `VALIDATION_ERROR`: Input validation error
- `TIMEOUT_ERROR`: Operation timeout
- `RESOURCE_UNAVAILABLE`: Required resource not available

**Example**:
```json
{
    "error_code": "TRANSCRIPTION_FAILED",
    "message": "Audio quality too low for accurate transcription",
    "timestamp": "2024-01-15T10:30:15Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440004",
    "retry_possible": true,
    "details": {
        "audio_quality_score": 0.2,
        "minimum_required": 0.5,
        "suggested_action": "Improve microphone setup or reduce background noise"
    }
}
```

### AgentMessage

Represents a message from the agent to the user.

```python
class AgentMessage(BaseModel):
    id: UUID = Field(..., description="Unique message identifier")
    session_id: UUID = Field(..., description="Associated session ID")
    message: str = Field(..., description="Agent message content")
    agent_name: str = Field(..., description="Name of the agent sending the message")
    timestamp: datetime = Field(..., description="Message timestamp")
    response_type: ResponseType = Field(..., description="Type of agent response")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Agent confidence in response")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")
```

**ResponseType Enum**:
- `answer`: Direct answer to user question
- `clarification`: Request for clarification from user
- `acknowledgment`: Acknowledgment of user input
- `status_update`: Update on task progress
- `error_response`: Response to handle an error condition

**Example**:
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440005",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "I found your account information. Your current balance is $1,250.75. Would you like to see your recent transactions?",
    "agent_name": "customer_service_agent",
    "timestamp": "2024-01-15T10:30:10Z",
    "response_type": "answer",
    "confidence": 0.95,
    "metadata": {
        "context_used": ["account_lookup_result"],
        "follow_up_suggested": true
    }
}
```

## Relationships

The models have the following relationships:

- **Session** 1:many **Utterance** (one session has multiple utterances)
- **Session** 1:many **Task** (one session has multiple tasks)
- **Task** 1:many **ToolInvocation** (one task may invoke multiple tools)
- **Agent** 1:many **Task** (one agent can execute multiple tasks)
- **Session** 1:many **AgentMessage** (one session has multiple agent messages)
- **Session** 1:many **ErrorEvent** (one session may have multiple errors)

## Computed Fields

Some models include computed fields derived from other data:

- `Task.progress`: Computed from internal executor events or explicit updates
- `Session.duration`: Computed as `end_time - start_time` when session is ended
- `Task.execution_time`: Computed as `completed_at - started_at` when task is completed

## Validation and Constraints

### Global Constraints

- All UUIDs must be valid UUID4 format
- All timestamps must be ISO 8601 format with timezone
- All confidence scores must be between 0.0 and 1.0
- Required fields cannot be null or empty

### Business Rules

- A session with status `ended` must have `end_time` set
- `Utterance.interrupted` true implies following agent audio was cut short
- `Task.result_summary` only present for final statuses (`completed`, `failed`, `cancelled`)
- Progress values must be monotonically increasing for active tasks

### Data Privacy

- Sensitive data is automatically redacted in logs and exports
- Audio data is not persisted by default
- Transcript data can be optionally redacted using configurable patterns

## Schema Versioning

All models include version information to support evolution:

- Current version: `1.0.0`
- Breaking changes require major version increment
- New optional fields require minor version increment
- Bug fixes require patch version increment

Schema versions are tracked in the `version` field where applicable and in the JSON Schema definitions in the contracts directory.