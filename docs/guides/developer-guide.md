# Developer Guide

This guide provides comprehensive information for developers working with the Call Center Voice Agent Accelerator.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Core Components](#core-components)
- [Building Custom Agents](#building-custom-agents)
- [Testing Strategies](#testing-strategies)
- [Deployment Guide](#deployment-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Azure subscription with Voice Live API access
- Azure Communication Services resource (for phone integration)
- Git for version control

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd call-center-voice-agent-accelerator-hackathon
   ```

2. **Set up the development environment**:
   ```bash
   cd server
   cp .env.sample .env
   # Edit .env with your Azure credentials
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Run tests**:
   ```bash
   uv run pytest
   ```

5. **Start the development server**:
   ```bash
   uv run server.py
   ```

6. **Open the web client**: http://localhost:8000

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile App     │    │   Phone Call    │
│   (Browser)     │    │  (Future)       │    │  (ACS/PSTN)     │
└─────┬───────────┘    └─────┬───────────┘    └─────┬───────────┘
      │                      │                      │
      │ WebSocket            │ WebSocket            │ ACS Events
      │                      │                      │
┌─────▼──────────────────────▼──────────────────────▼───────────┐
│                  Quart Web Server                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │   Stream    │ │  ACS Event  │ │      ACS Media          │  │
│  │   Handler   │ │   Handler   │ │      Handler            │  │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘  │
└─────┬──────────────────┬──────────────────┬───────────────────┘
      │                  │                  │
┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼────────┐
│  Session  │    │   Agent      │   │  Transcription│
│   Store   │    │   Runtime    │   │    Service    │
└───────────┘    └──────────────┘   └───────────────┘
      │                  │                  │
┌─────▼─────┐    ┌───────▼──────┐   ┌──────▼────────┐
│  Context  │    │     TTS      │   │   Redaction   │
│  Manager  │    │   Service    │   │    Service    │
└───────────┘    └──────────────┘   └───────────────┘
```

### Data Flow

1. **Audio Input**: User speaks → Audio captured → Base64 encoded → WebSocket
2. **Transcription**: Audio → Azure Voice Live API → Text
3. **Agent Processing**: Text → Agent Runtime → Intent extraction → Task planning
4. **Task Execution**: Tasks → Tool invocation → Results
5. **Response Generation**: Results → Agent response → TTS → Audio output
6. **Context Management**: All interactions → Context manager → Session store

### Key Design Patterns

- **Event-Driven Architecture**: WebSocket events drive all interactions
- **Async/Await**: Non-blocking I/O for high concurrency
- **Strategy Pattern**: Pluggable agent implementations
- **Circuit Breaker**: Resilient external service calls
- **Observer Pattern**: Event listeners for real-time updates

## Development Setup

### Environment Configuration

Create `.env` file in the `server/` directory:

```bash
# Required: Azure Voice Live API
AZURE_VOICE_LIVE_API_KEY=your_api_key
AZURE_VOICE_LIVE_ENDPOINT=https://your-region.api.cognitive.microsoft.com
VOICE_LIVE_MODEL=gpt-4o-mini

# Required for phone integration: Azure Communication Services
ACS_CONNECTION_STRING=endpoint=https://your-acs.communication.azure.com/;accesskey=...

# Optional: Development tunnel for phone testing
ACS_DEV_TUNNEL=https://your-tunnel.devtunnels.ms:8000

# Optional: Azure Identity (for production)
AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID=your_client_id

# Optional: Configuration
LOG_LEVEL=INFO
MAX_SESSION_DURATION=3600
CONTEXT_WINDOW_SIZE=50
```

### Development Tools

Install recommended VS Code extensions:

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.black-formatter",
        "charliermarsh.ruff",
        "ms-python.mypy-type-checker"
    ]
}
```

### Testing Setup

The project uses pytest with async support:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov=models --cov=services

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/

# Run tests in parallel
uv run pytest -n auto
```

## Core Components

### Session Management

Sessions represent a conversation between a user and agent:

```python
from models.session import Session
from services.session_store import SessionStore

# Create a new session
session = Session()
session_store = SessionStore()
await session_store.create_session(session)

# Retrieve session
session = await session_store.get_session(session_id)

# Update session status
await session_store.update_session_status(session_id, "ended")
```

### Agent Runtime

The agent runtime handles intelligent responses:

```python
from services.agent_runtime import AgentRuntime
from models.agent import Agent

# Initialize agent
agent = Agent(
    name="customer_service_agent",
    purpose="Handle customer inquiries",
    allowed_tools=["account_lookup", "balance_inquiry"]
)

runtime = AgentRuntime(agent)

# Process user input
response = await runtime.process_utterance(
    utterance_text="I need help with my account",
    session_context=context
)
```

### Transcription Service

Handle speech-to-text conversion:

```python
from services.transcription import TranscriptionService

transcription_service = TranscriptionService()

# Process audio data
result = await transcription_service.transcribe_audio(
    audio_data=base64_audio,
    format="pcm_16khz_16bit"
)

print(f"Transcribed: {result.text}")
print(f"Confidence: {result.confidence}")
```

### Text-to-Speech Service

Convert text responses to audio:

```python
from services.tts import TTSService

tts_service = TTSService()

# Generate speech
audio_data = await tts_service.synthesize_speech(
    text="Hello, how can I help you today?",
    voice="neural_voice_female"
)
```

### Error Handling

Robust error handling with retries:

```python
from services.retry import retry_with_backoff
from services.error_events import ErrorEventService

error_service = ErrorEventService()

@retry_with_backoff(max_retries=3)
async def call_external_api():
    # API call that might fail
    pass

try:
    result = await call_external_api()
except Exception as e:
    await error_service.log_error(
        error_code="API_CALL_FAILED",
        message=str(e),
        session_id=session_id
    )
```

## Building Custom Agents

### Agent Interface

Create custom agents by implementing the agent strategy interface:

```python
from models.agent import Agent
from typing import Dict, Any, List

class CustomAgent(Agent):
    def __init__(self):
        super().__init__(
            name="custom_agent",
            purpose="Handle specialized requests",
            allowed_tools=["custom_tool"]
        )
    
    async def process_intent(self, utterance: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user intent and return response plan."""
        # Custom intent processing logic
        return {
            "response": "Custom agent response",
            "tasks": [
                {
                    "description": "Execute custom task",
                    "tool": "custom_tool",
                    "parameters": {"param": "value"}
                }
            ]
        }
    
    async def can_handle_request(self, utterance: str) -> bool:
        """Determine if this agent can handle the request."""
        # Custom logic to determine capability
        return "custom" in utterance.lower()
```

### Tool Development

Create custom tools for agent use:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class Tool(ABC):
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool parameters."""
        pass

class AccountLookupTool(Tool):
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = parameters.get("customer_id")
        
        # Implement account lookup logic
        account_data = await self._lookup_account(customer_id)
        
        return {
            "status": "success",
            "data": account_data
        }
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier"
                }
            },
            "required": ["customer_id"]
        }
    
    async def _lookup_account(self, customer_id: str) -> Dict[str, Any]:
        # Implement actual lookup logic
        pass
```

### Agent Registration

Register custom agents and tools:

```python
from services.agent_runtime import AgentRuntime

# Register custom agent
runtime = AgentRuntime()
runtime.register_agent("custom_agent", CustomAgent())

# Register custom tool
runtime.register_tool("account_lookup", AccountLookupTool())
```

## Testing Strategies

### Unit Testing

Test individual components in isolation:

```python
import pytest
from unittest.mock import AsyncMock
from services.transcription import TranscriptionService

@pytest.mark.asyncio
async def test_transcription_service():
    service = TranscriptionService()
    
    # Mock external dependencies
    service._azure_client = AsyncMock()
    service._azure_client.transcribe.return_value = {
        "text": "Hello world",
        "confidence": 0.95
    }
    
    # Test transcription
    result = await service.transcribe_audio("fake_audio_data")
    
    assert result.text == "Hello world"
    assert result.confidence == 0.95
```

### Integration Testing

Test component interactions:

```python
@pytest.mark.asyncio
async def test_full_conversation_flow():
    # Setup
    session_store = SessionStore()
    agent_runtime = AgentRuntime()
    
    # Create session
    session = await session_store.create_session()
    
    # Process utterance
    utterance = Utterance(
        text="Hello, I need help",
        session_id=session.id
    )
    
    response = await agent_runtime.process_utterance(utterance)
    
    # Verify response
    assert response.message is not None
    assert len(response.tasks) > 0
```

### Contract Testing

Validate API contracts:

```python
import jsonschema
from jsonschema import validate

def test_session_schema():
    session_data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "active",
        "start_time": "2024-01-15T10:30:00Z",
        "version": "1.0.0"
    }
    
    schema = load_schema("session.schema.json")
    
    # Should not raise exception
    validate(instance=session_data, schema=schema)
```

### Performance Testing

Test system performance:

```python
import asyncio
import time

@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test handling multiple concurrent sessions."""
    
    async def create_session():
        # Simulate session creation and interaction
        start_time = time.time()
        
        # Session operations...
        
        end_time = time.time()
        return end_time - start_time
    
    # Create 10 concurrent sessions
    tasks = [create_session() for _ in range(10)]
    durations = await asyncio.gather(*tasks)
    
    # Verify performance requirements
    avg_duration = sum(durations) / len(durations)
    assert avg_duration < 2.0  # Under 2 seconds average
```

## Deployment Guide

### Local Development

```bash
# Start development server
cd server
uv run server.py

# Server runs on http://localhost:8000
# WebSocket endpoint: ws://localhost:8000/stream/{session_id}
```

### Docker Deployment

```bash
# Build image
docker build -t voice-agent .

# Run container
docker run --env-file .env -p 8000:8000 voice-agent
```

### Azure Container Apps

Deploy using Azure Developer CLI:

```bash
# Login to Azure
az login

# Initialize Azure Developer CLI
azd init

# Deploy to Azure
azd up
```

### Environment Variables

Production deployment requires:

```bash
# Azure services
AZURE_VOICE_LIVE_API_KEY=<from Azure Key Vault>
AZURE_VOICE_LIVE_ENDPOINT=<your region endpoint>
ACS_CONNECTION_STRING=<from Azure Key Vault>

# Identity and security
AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID=<managed identity>

# Performance tuning
MAX_SESSION_DURATION=3600
CONTEXT_WINDOW_SIZE=50
LOG_LEVEL=INFO

# Health checks
HEALTH_CHECK_INTERVAL=30
```

### Monitoring Setup

Configure Azure Application Insights:

```python
from azure.monitor.opentelemetry import configure_azure_monitor

# Configure telemetry
configure_azure_monitor(
    connection_string="InstrumentationKey=..."
)
```

## Best Practices

### Code Organization

```
server/
├── app/                    # Application layer
│   └── handler/           # Request handlers
├── models/                # Data models
├── services/              # Business logic
├── static/                # Web assets
├── tests/                 # Test suites
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── contract/         # Contract tests
└── server.py             # Application entry point
```

### Error Handling

1. **Use structured error codes** for programmatic handling
2. **Log errors with correlation IDs** for tracing
3. **Implement retry logic** for transient failures
4. **Provide user-friendly error messages**
5. **Monitor error rates** and patterns

### Performance Optimization

1. **Use async/await** for I/O operations
2. **Implement connection pooling** for external services
3. **Cache frequently accessed data**
4. **Stream large responses** instead of buffering
5. **Monitor memory usage** and optimize accordingly

### Security Considerations

1. **Never log sensitive data** (audio, credentials)
2. **Use Azure Managed Identity** in production
3. **Validate all input data** before processing
4. **Implement rate limiting** for public endpoints
5. **Use HTTPS/WSS** for all communications

### Testing Guidelines

1. **Write tests before implementation** (TDD)
2. **Mock external dependencies** in unit tests
3. **Test error conditions** and edge cases
4. **Maintain high test coverage** (>90% for critical paths)
5. **Run tests in CI/CD pipeline**

## Troubleshooting

### Common Issues

#### "Audio quality too low" errors

**Cause**: Poor microphone quality or background noise
**Solution**: 
- Check microphone settings
- Reduce background noise
- Use noise cancellation
- Increase audio gain

#### WebSocket connection drops

**Cause**: Network instability or server overload
**Solution**:
- Implement auto-reconnection
- Check network connectivity
- Monitor server resources
- Implement exponential backoff

#### Transcription delays

**Cause**: Azure service latency or audio processing issues
**Solution**:
- Use shorter audio chunks
- Optimize audio format
- Implement timeout handling
- Monitor service health

#### Agent responses slow

**Cause**: Complex processing or external API delays
**Solution**:
- Optimize agent logic
- Implement caching
- Use async processing
- Add progress indicators

### Debugging Tools

#### Log Analysis

```bash
# Filter logs by session
grep "session_id:550e8400" logs/app.log

# Monitor error rates
grep "ERROR" logs/app.log | wc -l

# Check performance metrics
grep "duration_ms" logs/app.log
```

#### WebSocket Testing

```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/stream/test-session-id

# Send test message
{"type": "session_control", "data": {"action": "start"}}
```

#### Health Checks

```bash
# Check service health
curl http://localhost:8000/health

# Check specific component
curl http://localhost:8000/health/transcription
```

### Performance Monitoring

Monitor these key metrics:

- **Response Time**: Session creation, transcription, agent processing
- **Error Rates**: By component and error type  
- **Concurrent Sessions**: Active session count
- **Resource Usage**: CPU, memory, network
- **External Dependencies**: Azure service health

### Support Resources

- **Documentation**: `/docs` directory
- **API Reference**: `/docs/api` directory
- **Issue Tracking**: GitHub Issues
- **Community**: Discussions tab
- **Azure Support**: For service-specific issues

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:

- Code style and formatting
- Pull request process
- Testing requirements
- Documentation standards
- Release procedures