# REST API

The REST API provides session management and status endpoints for voice agent interactions.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently uses environment variable configuration. Production deployments use Azure Managed Identity.

## Endpoints

### Health Check

**GET** `/health`

Returns service health and version information.

**Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "services": {
        "transcription": "available",
        "tts": "available",
        "agent_runtime": "available"
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `503 Service Unavailable`: One or more critical services are down

### Session Management

#### Create Session

**POST** `/sessions`

Creates a new voice session.

**Request Body**:
```json
{
    "agent_type": "customer_service_agent",
    "initial_context": {
        "customer_id": "CUST-12345",
        "priority": "normal"
    }
}
```

**Response**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "agent": {
        "name": "customer_service_agent",
        "version": "1.0.0",
        "capabilities": ["voice_transcription", "task_execution"]
    },
    "websocket_url": "ws://localhost:8000/stream/550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:
- `201 Created`: Session created successfully
- `400 Bad Request`: Invalid request parameters
- `429 Too Many Requests`: Rate limit exceeded

#### Get Session

**GET** `/sessions/{session_id}`

Retrieves session information and status.

**Path Parameters**:
- `session_id`: UUID of the session

**Response**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "start_time": "2024-01-15T10:30:00Z",
    "end_time": null,
    "agent": {
        "name": "customer_service_agent",
        "version": "1.0.0"
    },
    "statistics": {
        "utterance_count": 5,
        "task_count": 2,
        "duration_seconds": 127.3
    },
    "current_tasks": [
        {
            "task_id": "550e8400-e29b-41d4-a716-446655440002",
            "description": "Processing account lookup",
            "status": "in_progress",
            "progress": 0.65
        }
    ]
}
```

**Status Codes**:
- `200 OK`: Session found
- `404 Not Found`: Session does not exist

#### End Session

**POST** `/sessions/{session_id}/end`

Gracefully ends a voice session.

**Path Parameters**:
- `session_id`: UUID of the session

**Request Body**:
```json
{
    "reason": "user_request",
    "save_transcript": true
}
```

**Response**:
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "ended",
    "end_time": "2024-01-15T10:35:27Z",
    "summary": {
        "duration_seconds": 327.5,
        "utterance_count": 15,
        "task_count": 4,
        "tasks_completed": 4,
        "tasks_failed": 0
    }
}
```

**Status Codes**:
- `200 OK`: Session ended successfully
- `404 Not Found`: Session does not exist
- `409 Conflict`: Session already ended

### Task Management

#### List Session Tasks

**GET** `/sessions/{session_id}/tasks`

Lists all tasks for a session.

**Path Parameters**:
- `session_id`: UUID of the session

**Query Parameters**:
- `status`: Filter by task status (`pending`, `in_progress`, `completed`, `failed`)
- `limit`: Maximum number of tasks to return (default: 50)
- `offset`: Number of tasks to skip (default: 0)

**Response**:
```json
{
    "tasks": [
        {
            "task_id": "550e8400-e29b-41d4-a716-446655440002",
            "description": "Account information lookup",
            "status": "completed",
            "progress": 1.0,
            "started_at": "2024-01-15T10:30:15Z",
            "completed_at": "2024-01-15T10:30:17Z",
            "execution_time": 2.1,
            "result_summary": "Account details retrieved successfully"
        }
    ],
    "total_count": 4,
    "pagination": {
        "limit": 50,
        "offset": 0,
        "has_more": false
    }
}
```

**Status Codes**:
- `200 OK`: Tasks retrieved successfully
- `404 Not Found`: Session does not exist

#### Cancel Task

**POST** `/sessions/{session_id}/tasks/{task_id}/cancel`

Cancels a running task.

**Path Parameters**:
- `session_id`: UUID of the session
- `task_id`: UUID of the task

**Request Body**:
```json
{
    "reason": "user_requested_cancel"
}
```

**Response**:
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T10:30:25Z",
    "reason": "user_requested_cancel"
}
```

**Status Codes**:
- `200 OK`: Task cancelled successfully
- `404 Not Found`: Session or task does not exist
- `409 Conflict`: Task cannot be cancelled (already completed/failed)

### Text Fallback

#### Send Text Message

**POST** `/sessions/{session_id}/utterances`

Send a text message when audio is not available.

**Path Parameters**:
- `session_id`: UUID of the session

**Request Body**:
```json
{
    "text": "I need help with my account balance",
    "source": "text_fallback"
}
```

**Response**:
```json
{
    "utterance_id": "550e8400-e29b-41d4-a716-446655440001",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "I need help with my account balance",
    "confidence": 1.0,
    "timestamp": "2024-01-15T10:30:00Z",
    "source": "text_fallback"
}
```

**Status Codes**:
- `201 Created`: Utterance processed successfully
- `400 Bad Request`: Invalid text content
- `404 Not Found`: Session does not exist

### Export and Analytics

#### Session Export

**GET** `/sessions/{session_id}/export`

Export session transcript and analytics data.

**Path Parameters**:
- `session_id`: UUID of the session

**Query Parameters**:
- `format`: Export format (`json`, `txt`) (default: `json`)
- `include_audio`: Include audio data references (default: `false`)
- `redact_sensitive`: Apply redaction to sensitive data (default: `true`)

**Response** (JSON format):
```json
{
    "session": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "duration_seconds": 327.5,
        "utterance_count": 15
    },
    "transcript": [
        {
            "speaker": "user",
            "text": "Hello, I need help with my account",
            "timestamp": "2024-01-15T10:30:00Z",
            "confidence": 0.92
        },
        {
            "speaker": "agent",
            "text": "I'd be happy to help you with your account. What specific issue are you experiencing?",
            "timestamp": "2024-01-15T10:30:03Z"
        }
    ],
    "tasks": [
        {
            "description": "Account lookup",
            "status": "completed",
            "execution_time": 2.1
        }
    ],
    "metadata": {
        "agent_version": "1.0.0",
        "export_timestamp": "2024-01-15T10:40:00Z",
        "redaction_applied": true
    }
}
```

**Status Codes**:
- `200 OK`: Export generated successfully
- `404 Not Found`: Session does not exist
- `410 Gone`: Session data has been purged

## Error Responses

All error responses follow this format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error description",
        "details": {
            "field": "Specific validation error details"
        },
        "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

### Common Error Codes

- `INVALID_REQUEST`: Malformed request body or parameters
- `SESSION_NOT_FOUND`: Requested session does not exist
- `SESSION_ALREADY_ENDED`: Operation not allowed on ended session
- `TASK_NOT_FOUND`: Requested task does not exist
- `TASK_NOT_CANCELLABLE`: Task cannot be cancelled in current state
- `SERVICE_UNAVAILABLE`: Required service is temporarily unavailable
- `RATE_LIMIT_EXCEEDED`: Too many requests in time window

## Rate Limiting

Production deployments implement rate limiting:

- **Session Creation**: 10 sessions per minute per client
- **API Calls**: 100 requests per minute per session
- **Export Requests**: 5 exports per hour per session

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1642248600
```

## CORS Configuration

Development server allows all origins. Production should configure specific allowed origins:

```
Access-Control-Allow-Origin: https://yourdomain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## OpenAPI Specification

Complete OpenAPI 3.0 specification is available at `/docs` when running in development mode.