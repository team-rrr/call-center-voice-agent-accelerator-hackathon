# Error Handling

This document describes error handling patterns, error codes, and recovery strategies used in the Voice Agent system.

## Error Philosophy

The Voice Agent system follows these error handling principles:

1. **Fail Fast**: Detect and report errors early in the processing pipeline
2. **Graceful Degradation**: Continue operation when possible, fall back to alternative approaches
3. **User-Friendly**: Provide clear, actionable error messages to users
4. **Observable**: Log structured error information for debugging and monitoring
5. **Recoverable**: Design errors to be retryable where appropriate

## Error Categories

### Transient Errors

Temporary failures that may succeed on retry:

- Network connectivity issues
- Service timeouts
- Rate limiting
- Temporary resource unavailability

**Handling**: Automatic retry with exponential backoff

### Permanent Errors

Failures that will not succeed on retry:

- Invalid authentication credentials
- Malformed requests
- Unsupported operations
- Resource not found

**Handling**: Return error immediately, no retry

### Degraded Service Errors

Partial functionality failures:

- Audio quality too low for transcription
- Secondary service unavailable
- Feature not available in current context

**Handling**: Fall back to alternative approach, continue with reduced functionality

## Error Response Format

### REST API Errors

All REST API errors follow this format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error description",
        "details": {
            "field": "Specific validation error details",
            "constraint": "violated_constraint_name"
        },
        "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
        "timestamp": "2024-01-15T10:30:00Z",
        "retry_after": 5.0
    }
}
```

### WebSocket Error Events

WebSocket errors use the standard event format:

```json
{
    "type": "error",
    "data": {
        "error_code": "ERROR_CODE",
        "message": "Human-readable error description",
        "severity": "low|medium|high|critical",
        "retry_possible": true,
        "retry_delay": 2.0,
        "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
        "context": {
            "component": "transcription",
            "operation": "speech_to_text",
            "parameters": {}
        },
        "suggested_action": "Check microphone and reduce background noise"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Error Codes

### Authentication & Authorization (AUTH_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `AUTH_INVALID_CREDENTIALS` | Invalid API key or token | No | Update credentials |
| `AUTH_TOKEN_EXPIRED` | Authentication token expired | Yes | Refresh token |
| `AUTH_INSUFFICIENT_PERMISSIONS` | User lacks required permissions | No | Contact administrator |
| `AUTH_RATE_LIMITED` | Too many authentication attempts | Yes | Wait and retry |

### Validation Errors (VALIDATION_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `VALIDATION_INVALID_REQUEST` | Malformed request body | No | Fix request format |
| `VALIDATION_MISSING_FIELD` | Required field missing | No | Provide missing data |
| `VALIDATION_INVALID_UUID` | Invalid UUID format | No | Correct UUID format |
| `VALIDATION_INVALID_TIMESTAMP` | Invalid timestamp format | No | Use ISO 8601 format |
| `VALIDATION_OUT_OF_RANGE` | Value outside allowed range | No | Adjust value |

### Session Errors (SESSION_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `SESSION_NOT_FOUND` | Session does not exist | No | Create new session |
| `SESSION_ALREADY_ENDED` | Operation on ended session | No | Create new session |
| `SESSION_TIMEOUT` | Session exceeded time limit | No | Create new session |
| `SESSION_LIMIT_EXCEEDED` | Too many concurrent sessions | Yes | Wait or close other sessions |
| `SESSION_INVALID_STATE` | Invalid state transition | No | Check session status |

### Audio Processing Errors (AUDIO_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `AUDIO_FORMAT_UNSUPPORTED` | Unsupported audio format | No | Use supported format |
| `AUDIO_QUALITY_TOO_LOW` | Audio quality insufficient | Yes | Improve audio quality |
| `AUDIO_SIZE_EXCEEDED` | Audio data too large | No | Reduce audio size |
| `AUDIO_STREAM_INTERRUPTED` | Audio stream connection lost | Yes | Reconnect and resume |
| `AUDIO_ENCODING_ERROR` | Audio encoding/decoding error | Yes | Check audio format |

### Transcription Errors (TRANSCRIPTION_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `TRANSCRIPTION_FAILED` | Speech-to-text processing failed | Yes | Retry with better audio |
| `TRANSCRIPTION_NO_SPEECH` | No speech detected in audio | No | Provide audio with speech |
| `TRANSCRIPTION_LANGUAGE_UNSUPPORTED` | Language not supported | No | Use supported language |
| `TRANSCRIPTION_TIMEOUT` | Transcription process timeout | Yes | Retry operation |
| `TRANSCRIPTION_SERVICE_UNAVAILABLE` | Transcription service down | Yes | Wait and retry |

### Text-to-Speech Errors (TTS_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `TTS_FAILED` | Text-to-speech synthesis failed | Yes | Retry operation |
| `TTS_TEXT_TOO_LONG` | Text exceeds length limit | No | Reduce text length |
| `TTS_VOICE_UNAVAILABLE` | Requested voice not available | No | Use different voice |
| `TTS_SERVICE_UNAVAILABLE` | TTS service temporarily down | Yes | Wait and retry |
| `TTS_UNSUPPORTED_LANGUAGE` | Language not supported for TTS | No | Use supported language |

### Agent Runtime Errors (AGENT_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `AGENT_RUNTIME_ERROR` | General agent execution error | Yes | Retry operation |
| `AGENT_NOT_FOUND` | Specified agent not available | No | Use different agent |
| `AGENT_INITIALIZATION_FAILED` | Agent failed to initialize | Yes | Restart agent |
| `AGENT_TIMEOUT` | Agent response timeout | Yes | Retry with longer timeout |
| `AGENT_CONTEXT_OVERFLOW` | Agent context too large | No | Reduce context size |

### Task Execution Errors (TASK_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `TASK_EXECUTION_FAILED` | Task execution error | Yes | Retry task |
| `TASK_NOT_FOUND` | Task does not exist | No | Create new task |
| `TASK_NOT_CANCELLABLE` | Task cannot be cancelled | No | Wait for completion |
| `TASK_TIMEOUT` | Task execution timeout | Yes | Retry with longer timeout |
| `TASK_DEPENDENCY_FAILED` | Required task dependency failed | Yes | Retry dependencies |

### Tool Invocation Errors (TOOL_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `TOOL_NOT_FOUND` | Specified tool not available | No | Use different tool |
| `TOOL_EXECUTION_FAILED` | Tool execution error | Yes | Retry operation |
| `TOOL_INVALID_PARAMETERS` | Invalid tool parameters | No | Correct parameters |
| `TOOL_PERMISSION_DENIED` | Tool access not permitted | No | Use authorized tool |
| `TOOL_TIMEOUT` | Tool execution timeout | Yes | Retry operation |

### System Errors (SYSTEM_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `SYSTEM_OVERLOADED` | System temporarily overloaded | Yes | Wait and retry |
| `SYSTEM_MAINTENANCE` | System under maintenance | Yes | Wait for maintenance completion |
| `SYSTEM_RESOURCE_EXHAUSTED` | System resources exhausted | Yes | Wait for resources |
| `SYSTEM_CONFIGURATION_ERROR` | System misconfiguration | No | Contact administrator |
| `SYSTEM_INTERNAL_ERROR` | Unexpected internal error | Yes | Retry operation |

### Network Errors (NETWORK_*)

| Code | Description | Retry | Action |
|------|-------------|-------|--------|
| `NETWORK_CONNECTION_FAILED` | Network connection failed | Yes | Check network connectivity |
| `NETWORK_TIMEOUT` | Network operation timeout | Yes | Retry with longer timeout |
| `NETWORK_DNS_RESOLUTION_FAILED` | DNS resolution failed | Yes | Check DNS configuration |
| `NETWORK_SSL_ERROR` | SSL/TLS connection error | Yes | Check certificates |
| `NETWORK_PROXY_ERROR` | Proxy connection error | Yes | Check proxy settings |

## Error Severity Levels

### Low Severity

Non-critical issues that don't impact core functionality:

- Partial data unavailable
- Non-essential features disabled
- Performance degradation

**Impact**: User experience slightly affected

### Medium Severity

Issues that impact some functionality but allow operation to continue:

- Transcription quality reduced
- Secondary features unavailable
- Temporary service degradation

**Impact**: Some features may not work as expected

### High Severity

Issues that significantly impact functionality:

- Core service failures
- Authentication problems
- Data corruption

**Impact**: Major features unavailable

### Critical Severity

Issues that prevent system operation:

- Complete service failure
- Security breaches
- Data loss

**Impact**: System unusable

## Retry Strategies

### Exponential Backoff

Used for transient errors:

```python
def retry_with_backoff(operation, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return operation()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

### Circuit Breaker

Used for service dependencies:

- **Closed**: Normal operation, all requests pass through
- **Open**: Service is failing, requests fail immediately
- **Half-Open**: Testing if service has recovered

### Fallback Strategies

#### Audio Processing Fallback

1. High-quality transcription fails → Try with reduced quality settings
2. Real-time transcription fails → Fall back to batch processing
3. Audio processing fails → Fall back to text-only mode

#### Agent Response Fallback

1. Primary agent fails → Use backup agent
2. Complex reasoning fails → Use simple response templates
3. Tool execution fails → Provide manual instructions

#### TTS Fallback

1. Neural voice fails → Use standard voice
2. TTS service fails → Return text-only response
3. Audio streaming fails → Pre-generate audio files

## Error Logging

### Structured Logging Format

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "ERROR",
    "component": "transcription",
    "operation": "speech_to_text",
    "error_code": "TRANSCRIPTION_FAILED",
    "message": "Audio quality too low for transcription",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "context": {
        "audio_quality_score": 0.2,
        "minimum_required": 0.5,
        "retry_count": 1
    },
    "stack_trace": "...",
    "request_id": "req_456"
}
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARN**: Warning conditions that don't prevent operation
- **ERROR**: Error conditions that impact functionality
- **FATAL**: Critical errors that prevent system operation

### Sensitive Data Redaction

All logs automatically redact:

- Audio data
- Authentication tokens
- Personal information (12+ digit sequences)
- API keys and secrets

## Monitoring and Alerting

### Error Rate Monitoring

- Overall error rate threshold: < 5%
- Critical error rate threshold: < 1%
- Service-specific error rates tracked separately

### Alert Conditions

- **Immediate**: Critical errors, security incidents
- **Within 5 minutes**: High error rates, service failures
- **Within 15 minutes**: Performance degradation, medium error rates
- **Daily digest**: Low severity issues, trending problems

### Error Dashboards

Key metrics to monitor:

- Error rate by component
- Error distribution by type
- Recovery time trends
- User impact metrics

## Client Error Handling

### JavaScript Example

```javascript
class VoiceAgentClient {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.retryCount = 0;
        this.maxRetries = 3;
    }
    
    async handleError(error) {
        const errorData = error.data;
        
        // Log error for debugging
        console.error('Voice Agent Error:', errorData);
        
        // Handle based on error type
        switch(errorData.error_code) {
            case 'AUDIO_QUALITY_TOO_LOW':
                this.showUserMessage('Please check your microphone and reduce background noise');
                return; // Don't retry
                
            case 'TRANSCRIPTION_FAILED':
                if (errorData.retry_possible && this.retryCount < this.maxRetries) {
                    this.retryCount++;
                    setTimeout(() => this.retryLastOperation(), errorData.retry_delay * 1000);
                } else {
                    this.fallbackToTextMode();
                }
                break;
                
            case 'SESSION_TIMEOUT':
                this.restartSession();
                break;
                
            default:
                this.showGenericError(errorData.message);
        }
    }
    
    async retryLastOperation() {
        // Implement retry logic
    }
    
    fallbackToTextMode() {
        // Switch to text-only interaction
    }
    
    restartSession() {
        // Create new session
    }
}
```

### Python Client Example

```python
import asyncio
import logging
from typing import Dict, Any

class ErrorHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_counts: Dict[str, int] = {}
    
    async def handle_error(self, error_data: Dict[str, Any], operation_id: str):
        error_code = error_data.get('error_code')
        
        # Log structured error
        logging.error(
            "Voice agent error",
            extra={
                'error_code': error_code,
                'correlation_id': error_data.get('correlation_id'),
                'retry_possible': error_data.get('retry_possible', False)
            }
        )
        
        # Handle retryable errors
        if error_data.get('retry_possible') and self._should_retry(operation_id):
            delay = error_data.get('retry_delay', 1.0)
            await asyncio.sleep(delay)
            return True  # Indicate retry should happen
        
        # Handle non-retryable errors
        await self._handle_permanent_error(error_code, error_data)
        return False  # No retry
    
    def _should_retry(self, operation_id: str) -> bool:
        count = self.retry_counts.get(operation_id, 0)
        if count < self.max_retries:
            self.retry_counts[operation_id] = count + 1
            return True
        return False
    
    async def _handle_permanent_error(self, error_code: str, error_data: Dict[str, Any]):
        # Handle specific permanent errors
        if error_code == 'SESSION_NOT_FOUND':
            await self.create_new_session()
        elif error_code == 'AUDIO_FORMAT_UNSUPPORTED':
            await self.switch_audio_format()
        else:
            # Generic error handling
            logging.error(f"Permanent error: {error_data.get('message')}")
```

## Best Practices

### For API Consumers

1. **Always check error responses** and handle them appropriately
2. **Implement exponential backoff** for retryable errors
3. **Use correlation IDs** for tracking related requests
4. **Provide user-friendly error messages** rather than exposing technical details
5. **Have fallback strategies** for critical functionality
6. **Monitor error rates** and investigate patterns

### For Service Developers

1. **Return consistent error formats** across all endpoints
2. **Use appropriate HTTP status codes** for REST APIs
3. **Include correlation IDs** in all error responses
4. **Log errors with sufficient context** for debugging
5. **Make errors retryable when appropriate**
6. **Implement circuit breakers** for external dependencies

### For Operations Teams

1. **Set up comprehensive monitoring** for error rates and patterns
2. **Create runbooks** for common error scenarios
3. **Implement automated alerting** for critical errors
4. **Monitor downstream dependencies** and their error rates
5. **Have escalation procedures** for different error severities