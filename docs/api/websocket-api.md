# WebSocket API

The primary interface for real-time voice interaction uses WebSocket connections for bidirectional audio streaming and event communication.

## Connection

**Endpoint**: `ws://localhost:8000/stream/{session_id}`

**Parameters**:
- `session_id`: UUID identifying the voice session

**Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/stream/550e8400-e29b-41d4-a716-446655440000');
```

## Message Format

All WebSocket messages use JSON format:

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

### Audio Data
Send raw audio data for transcription:

```json
{
    "type": "audio",
    "data": {
        "audio": "base64-encoded-audio-data",
        "format": "pcm_16khz_16bit"
    }
}
```

### Session Control
Start or stop the session:

```json
{
    "type": "session_control",
    "data": {
        "action": "start|stop"
    }
}
```

### Barge-in (Interruption)
Interrupt the agent's current response:

```json
{
    "type": "barge_in",
    "data": {
        "reason": "user_speaking"
    }
}
```

## Server → Client Events

### Transcript Events

**Partial Transcript** (real-time):
```json
{
    "type": "transcript_partial",
    "data": {
        "text": "Hello, I need help with...",
        "confidence": 0.85
    }
}
```

**Final Transcript**:
```json
{
    "type": "transcript_final",
    "data": {
        "utterance_id": "550e8400-e29b-41d4-a716-446655440001",
        "text": "Hello, I need help with my account",
        "confidence": 0.92,
        "interrupted": false
    }
}
```

### Agent Response Events

**Agent Message**:
```json
{
    "type": "agent_message",
    "data": {
        "message": "I'd be happy to help you with your account. What specific issue are you experiencing?",
        "agent_name": "customer_service_agent",
        "response_type": "clarification"
    }
}
```

**Audio Response**:
```json
{
    "type": "audio_response",
    "data": {
        "audio": "base64-encoded-audio-data",
        "format": "pcm_16khz_16bit",
        "duration_ms": 3500
    }
}
```

### Task Events

**Task Started**:
```json
{
    "type": "task_started", 
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002",
        "description": "Looking up account information",
        "estimated_duration": 2.5
    }
}
```

**Task Progress**:
```json
{
    "type": "task_progress",
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002", 
        "progress": 0.65,
        "status": "Accessing account database..."
    }
}
```

**Task Completed**:
```json
{
    "type": "task_completed",
    "data": {
        "task_id": "550e8400-e29b-41d4-a716-446655440002",
        "result": "Account information retrieved successfully",
        "execution_time": 2.1
    }
}
```

### Session Events

**Session Started**:
```json
{
    "type": "session_started",
    "data": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "agent_name": "customer_service_agent",
        "capabilities": ["voice_transcription", "task_execution", "knowledge_base"]
    }
}
```

**Session Ended**:
```json
{
    "type": "session_ended",
    "data": {
        "reason": "user_hangup|agent_completion|timeout|error",
        "duration": 127.3,
        "utterance_count": 12,
        "task_count": 3
    }
}
```

### Error Events

**Error Event**:
```json
{
    "type": "error",
    "data": {
        "error_code": "TRANSCRIPTION_FAILED",
        "message": "Audio quality too low for transcription",
        "retry_possible": true,
        "correlation_id": "550e8400-e29b-41d4-a716-446655440003"
    }
}
```

## Audio Format Requirements

**Supported Formats**:
- PCM 16-bit, 16kHz (recommended)
- PCM 16-bit, 8kHz
- Opus codec (when WebRTC enabled)

**Encoding**: Base64 for JSON transport

**Sample Rate**: 16kHz preferred for optimal transcription quality

## Connection Lifecycle

1. **Connect**: Client establishes WebSocket connection
2. **Initialize**: Server sends `session_started` event
3. **Stream**: Bidirectional audio and event exchange
4. **Terminate**: Either party can end with `session_control` or close connection
5. **Cleanup**: Server sends `session_ended` event and closes gracefully

## Error Handling

- **Transient Errors**: Client should retry with exponential backoff
- **Fatal Errors**: Connection will be closed by server
- **Audio Errors**: Fallback to text-only mode when possible

## Rate Limiting

Current implementation has no explicit rate limiting, but production deployments should implement:

- Maximum concurrent connections per client
- Audio data rate limiting (MB/minute)
- Event frequency limits

## Security Considerations

- Use WSS (WebSocket Secure) in production
- Validate all audio data size limits
- Implement connection timeout policies
- Audio data is not persisted by default (privacy by design)

## Example JavaScript Client

```javascript
class VoiceAgentClient {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
    }
    
    connect() {
        this.ws = new WebSocket(`ws://localhost:8000/stream/${this.sessionId}`);
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onopen = () => {
            this.sendControl('start');
        };
    }
    
    sendAudio(audioData) {
        this.ws.send(JSON.stringify({
            type: 'audio',
            data: {
                audio: audioData,
                format: 'pcm_16khz_16bit'
            }
        }));
    }
    
    sendControl(action) {
        this.ws.send(JSON.stringify({
            type: 'session_control',
            data: { action }
        }));
    }
    
    handleMessage(message) {
        switch(message.type) {
            case 'transcript_final':
                console.log('User said:', message.data.text);
                break;
            case 'agent_message':
                console.log('Agent:', message.data.message);
                break;
            case 'error':
                console.error('Error:', message.data.message);
                break;
        }
    }
}
```

See [Event Types](event-types.md) for complete event schema definitions.