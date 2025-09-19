# Event Types

This document defines all WebSocket event types and their message formats used in the Voice Agent system.

## Message Structure

All WebSocket messages follow this base structure:

```json
{
    "type": "event_type",
    "data": {
        // Event-specific payload
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Client → Server Events

### audio

Client sends audio data for transcription.

**Type**: `audio`

**Data Schema**:
```json
{
    "audio": "base64-encoded-audio-data",
    "format": "pcm_16khz_16bit|pcm_8khz_16bit|opus",
    "chunk_index": 123,
    "final": false
}
```

**Fields**:
- `audio`: Base64-encoded raw audio data
- `format`: Audio format specification
- `chunk_index`: Sequential chunk number for ordering (optional)
- `final`: Whether this is the final audio chunk for current utterance

**Example**:
```json
{
    "type": "audio",
    "data": {
        "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
        "format": "pcm_16khz_16bit",
        "chunk_index": 15,
        "final": false
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### session_control

Client controls session lifecycle.

**Type**: `session_control`

**Data Schema**:
```json
{
    "action": "start|stop|pause|resume",
    "reason": "user_request|timeout|error"
}
```

**Actions**:
- `start`: Begin session processing
- `stop`: End session gracefully
- `pause`: Temporarily pause processing
- `resume`: Resume paused session

**Example**:
```json
{
    "type": "session_control",
    "data": {
        "action": "stop",
        "reason": "user_request"
    },
    "timestamp": "2024-01-15T10:35:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### barge_in

Client interrupts agent speech/processing.

**Type**: `barge_in`

**Data Schema**:
```json
{
    "reason": "user_speaking|user_request|timeout",
    "interrupt_point": "agent_speaking|task_executing|waiting_for_input"
}
```

**Example**:
```json
{
    "type": "barge_in",
    "data": {
        "reason": "user_speaking",
        "interrupt_point": "agent_speaking"
    },
    "timestamp": "2024-01-15T10:30:15Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### text_message

Client sends text message as fallback when audio unavailable.

**Type**: `text_message`

**Data Schema**:
```json
{
    "text": "Message content",
    "source": "keyboard|voice_fallback|system"
}
```

**Example**:
```json
{
    "type": "text_message",
    "data": {
        "text": "I need help with my account balance",
        "source": "keyboard"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Server → Client Events

### session_started

Server confirms session initialization.

**Type**: `session_started`

**Data Schema**:
```json
{
    "session_id": "uuid",
    "agent": {
        "name": "agent_name",
        "version": "1.0.0",
        "purpose": "Agent description"
    },
    "capabilities": ["voice_transcription", "task_execution", "knowledge_base"],
    "configuration": {
        "audio_format": "pcm_16khz_16bit",
        "language": "en-US",
        "max_session_duration": 3600
    }
}
```

**Example**:
```json
{
    "type": "session_started",
    "data": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent": {
            "name": "customer_service_agent",
            "version": "1.0.0",
            "purpose": "Handle customer service inquiries and account operations"
        },
        "capabilities": ["voice_transcription", "task_execution", "knowledge_base"],
        "configuration": {
            "audio_format": "pcm_16khz_16bit",
            "language": "en-US",
            "max_session_duration": 3600
        }
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### session_ended

Server confirms session termination.

**Type**: `session_ended`

**Data Schema**:
```json
{
    "reason": "user_hangup|agent_completion|timeout|error|system_shutdown",
    "duration": 127.3,
    "statistics": {
        "utterance_count": 12,
        "task_count": 3,
        "tasks_completed": 3,
        "tasks_failed": 0,
        "total_audio_duration": 95.2
    },
    "final_status": "completed|interrupted|error"
}
```

**Example**:
```json
{
    "type": "session_ended",
    "data": {
        "reason": "user_hangup",
        "duration": 127.3,
        "statistics": {
            "utterance_count": 12,
            "task_count": 3,
            "tasks_completed": 3,
            "tasks_failed": 0,
            "total_audio_duration": 95.2
        },
        "final_status": "completed"
    },
    "timestamp": "2024-01-15T10:32:07Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### transcript_partial

Server sends real-time partial transcription.

**Type**: `transcript_partial`

**Data Schema**:
```json
{
    "text": "Partial transcription text...",
    "confidence": 0.85,
    "is_final": false,
    "alternatives": [
        {
            "text": "Alternative transcription",
            "confidence": 0.72
        }
    ]
}
```

**Example**:
```json
{
    "type": "transcript_partial",
    "data": {
        "text": "Hello, I need help with...",
        "confidence": 0.85,
        "is_final": false,
        "alternatives": [
            {
                "text": "Hello, I need help...",
                "confidence": 0.72
            }
        ]
    },
    "timestamp": "2024-01-15T10:30:02Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### transcript_final

Server sends final transcription result.

**Type**: `transcript_final`

**Data Schema**:
```json
{
    "utterance_id": "uuid",
    "text": "Final transcribed text",
    "confidence": 0.92,
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": "2024-01-15T10:30:03Z",
    "interrupted": false,
    "redacted_text": "Final transcribed text with [REDACTED] sensitive data"
}
```

**Example**:
```json
{
    "type": "transcript_final",
    "data": {
        "utterance_id": "550e8400-e29b-41d4-a716-446655440001",
        "text": "Hello, I need help with my account",
        "confidence": 0.92,
        "start_time": "2024-01-15T10:30:00Z",
        "end_time": "2024-01-15T10:30:03Z",
        "interrupted": false,
        "redacted_text": "Hello, I need help with my account"
    },
    "timestamp": "2024-01-15T10:30:03Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### agent_message

Server sends agent response message.

**Type**: `agent_message`

**Data Schema**:
```json
{
    "message_id": "uuid",
    "message": "Agent response text",
    "agent_name": "customer_service_agent",
    "response_type": "answer|clarification|acknowledgment|status_update|error_response",
    "confidence": 0.95,
    "context": {
        "referenced_tasks": ["task_id_1", "task_id_2"],
        "knowledge_sources": ["account_database", "policy_knowledge_base"]
    },
    "follow_up_suggested": true
}
```

**Example**:
```json
{
    "type": "agent_message",
    "data": {
        "message_id": "550e8400-e29b-41d4-a716-446655440005",
        "message": "I'd be happy to help you with your account. What specific issue are you experiencing?",
        "agent_name": "customer_service_agent",
        "response_type": "clarification",
        "confidence": 0.95,
        "context": {
            "referenced_tasks": [],
            "knowledge_sources": ["greeting_templates"]
        },
        "follow_up_suggested": true
    },
    "timestamp": "2024-01-15T10:30:05Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### audio_response

Server sends synthesized audio response.

**Type**: `audio_response`

**Data Schema**:
```json
{
    "audio": "base64-encoded-audio-data",
    "format": "pcm_16khz_16bit|opus",
    "duration_ms": 3500,
    "text": "Original text that was synthesized",
    "voice_settings": {
        "voice_name": "neural_voice_female",
        "speed": 1.0,
        "pitch": 0.0
    },
    "chunk_index": 1,
    "total_chunks": 3
}
```

**Example**:
```json
{
    "type": "audio_response",
    "data": {
        "audio": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
        "format": "pcm_16khz_16bit",
        "duration_ms": 3500,
        "text": "I'd be happy to help you with your account.",
        "voice_settings": {
            "voice_name": "neural_voice_female",
            "speed": 1.0,
            "pitch": 0.0
        },
        "chunk_index": 1,
        "total_chunks": 1
    },
    "timestamp": "2024-01-15T10:30:06Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### task_started

Server notifies that a task has begun execution.

**Type**: `task_started`

**Data Schema**:
```json
{
    "task_id": "uuid",
    "description": "Human-readable task description",
    "agent_name": "customer_service_agent",
    "estimated_duration": 2.5,
    "tools_required": ["account_lookup", "balance_inquiry"],
    "priority": "normal|high|low"
}
```

**Example**:
```json
{
    "type": "task_started",
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002",
        "description": "Looking up account information",
        "agent_name": "customer_service_agent",
        "estimated_duration": 2.5,
        "tools_required": ["account_lookup"],
        "priority": "normal"
    },
    "timestamp": "2024-01-15T10:30:06Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### task_progress

Server provides task execution progress updates.

**Type**: `task_progress`

**Data Schema**:
```json
{
    "task_id": "uuid",
    "progress": 0.65,
    "status_message": "Accessing account database...",
    "current_step": "data_retrieval",
    "steps_completed": 2,
    "total_steps": 3,
    "estimated_remaining": 1.2
}
```

**Example**:
```json
{
    "type": "task_progress",
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002",
        "progress": 0.65,
        "status_message": "Accessing account database...",
        "current_step": "data_retrieval",
        "steps_completed": 2,
        "total_steps": 3,
        "estimated_remaining": 1.2
    },
    "timestamp": "2024-01-15T10:30:07Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### task_completed

Server notifies that a task has finished execution.

**Type**: `task_completed`

**Data Schema**:
```json
{
    "task_id": "uuid",
    "status": "completed|failed|cancelled",
    "result": {
        "summary": "Task execution result summary",
        "data": {
            // Task-specific result data
        }
    },
    "execution_time": 2.1,
    "tools_used": [
        {
            "tool_name": "account_lookup",
            "execution_time": 1.8,
            "status": "success"
        }
    ],
    "error_message": null
}
```

**Example**:
```json
{
    "type": "task_completed",
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002",
        "status": "completed",
        "result": {
            "summary": "Account information retrieved successfully",
            "data": {
                "account_status": "active",
                "balance": 1250.75,
                "last_transaction_date": "2024-01-14"
            }
        },
        "execution_time": 2.1,
        "tools_used": [
            {
                "tool_name": "account_lookup",
                "execution_time": 1.8,
                "status": "success"
            }
        ],
        "error_message": null
    },
    "timestamp": "2024-01-15T10:30:08Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### error

Server reports an error condition.

**Type**: `error`

**Data Schema**:
```json
{
    "error_code": "ERROR_CODE",
    "message": "Human-readable error description",
    "severity": "low|medium|high|critical",
    "retry_possible": true,
    "retry_delay": 2.0,
    "correlation_id": "uuid",
    "context": {
        "component": "transcription|tts|agent_runtime|task_executor",
        "operation": "specific_operation_name",
        "parameters": {}
    },
    "suggested_action": "Specific user action recommendation"
}
```

**Common Error Codes**:
- `TRANSCRIPTION_FAILED`: Audio transcription error
- `TTS_FAILED`: Text-to-speech synthesis error  
- `AGENT_RUNTIME_ERROR`: Agent execution error
- `TASK_EXECUTION_FAILED`: Task execution error
- `AUDIO_FORMAT_UNSUPPORTED`: Unsupported audio format
- `SESSION_TIMEOUT`: Session exceeded time limits
- `RESOURCE_UNAVAILABLE`: Required service unavailable

**Example**:
```json
{
    "type": "error",
    "data": {
        "error_code": "TRANSCRIPTION_FAILED",
        "message": "Audio quality too low for accurate transcription",
        "severity": "medium",
        "retry_possible": true,
        "retry_delay": 1.0,
        "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
        "context": {
            "component": "transcription",
            "operation": "speech_to_text",
            "parameters": {
                "audio_quality_score": 0.2
            }
        },
        "suggested_action": "Please check your microphone and reduce background noise"
    },
    "timestamp": "2024-01-15T10:30:15Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### clarification_needed

Server requests clarification from user.

**Type**: `clarification_needed`

**Data Schema**:
```json
{
    "question": "Clarification question text",
    "context": "Why clarification is needed",
    "suggestions": ["suggestion1", "suggestion2"],
    "timeout": 30,
    "related_task_id": "uuid"
}
```

**Example**:
```json
{
    "type": "clarification_needed",
    "data": {
        "question": "Which account would you like me to check - your checking or savings account?",
        "context": "Multiple accounts found for the provided information",
        "suggestions": ["checking account", "savings account", "both accounts"],
        "timeout": 30,
        "related_task_id": "550e8400-e29b-41d4-a716-446655440002"
    },
    "timestamp": "2024-01-15T10:30:10Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### agent_plan

Server shares agent's execution plan with user.

**Type**: `agent_plan`

**Data Schema**:
```json
{
    "plan_id": "uuid", 
    "description": "Overall plan description",
    "steps": [
        {
            "step_number": 1,
            "description": "Step description",
            "estimated_duration": 2.0,
            "required_tools": ["tool1", "tool2"]
        }
    ],
    "total_estimated_duration": 5.5,
    "user_confirmation_required": false
}
```

**Example**:
```json
{
    "type": "agent_plan",
    "data": {
        "plan_id": "550e8400-e29b-41d4-a716-446655440006",
        "description": "I'll help you check your account balance and recent transactions",
        "steps": [
            {
                "step_number": 1,
                "description": "Look up your account information",
                "estimated_duration": 2.0,
                "required_tools": ["account_lookup"]
            },
            {
                "step_number": 2,
                "description": "Retrieve recent transaction history",
                "estimated_duration": 1.5,
                "required_tools": ["transaction_history"]
            }
        ],
        "total_estimated_duration": 3.5,
        "user_confirmation_required": false
    },
    "timestamp": "2024-01-15T10:30:05Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Event Flow Patterns

### Typical Session Flow

1. Client establishes WebSocket connection
2. Server sends `session_started`
3. Client sends `session_control` with action "start"
4. Client streams `audio` events
5. Server responds with `transcript_partial` and `transcript_final`
6. Server sends `agent_plan` (optional)
7. Server sends `task_started`, `task_progress`, `task_completed`
8. Server sends `agent_message` and `audio_response`
9. Repeat steps 4-8 for continued conversation
10. Client sends `session_control` with action "stop"
11. Server sends `session_ended`

### Error Handling Pattern

1. Error occurs in any component
2. Server sends `error` event with appropriate code
3. If `retry_possible` is true, client may retry operation
4. Server may send `clarification_needed` for user input errors
5. Session continues unless error is critical

### Barge-in Pattern

1. Client detects user speaking during agent response
2. Client sends `barge_in` event
3. Server stops current audio output
4. Server cancels any in-progress TTS
5. Server resumes listening for user input
6. Normal flow continues with user's new input

## Event Validation

All events are validated against JSON Schema definitions available in `specs/001-what-a-voice/contracts/`. Key validation rules:

- All UUIDs must be valid UUID4 format
- Timestamps must be ISO 8601 with timezone
- Audio data must be valid base64 encoding
- Confidence scores must be 0.0-1.0
- Progress values must be 0.0-1.0 and monotonically increasing
- Error codes must be from the predefined set
- Required fields cannot be null or empty

## Backward Compatibility

Events follow semantic versioning:

- **Major Version Changes**: Breaking schema changes, removed fields
- **Minor Version Changes**: New optional fields, new event types  
- **Patch Version Changes**: Bug fixes, clarified documentation

Current event schema version: `1.0.0`