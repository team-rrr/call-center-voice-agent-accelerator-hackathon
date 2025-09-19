# Usage Examples

This document provides practical examples of using the Voice Agent system in different scenarios.

## Table of Contents

- [Web Client Integration](#web-client-integration)
- [REST API Usage](#rest-api-usage)
- [WebSocket Client Development](#websocket-client-development)
- [Custom Agent Development](#custom-agent-development)
- [Phone Integration](#phone-integration)
- [Production Deployment](#production-deployment)

## Web Client Integration

### Basic HTML/JavaScript Client

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Agent Client</title>
</head>
<body>
    <button id="startBtn">Start Conversation</button>
    <button id="stopBtn" disabled>Stop Conversation</button>
    <div id="transcript"></div>
    <div id="response"></div>

    <script>
        class VoiceAgentClient {
            constructor() {
                this.ws = null;
                this.sessionId = null;
                this.mediaRecorder = null;
                this.audioChunks = [];
            }

            async startConversation() {
                // Create session
                const response = await fetch('/sessions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent_type: 'customer_service_agent' })
                });
                
                const session = await response.json();
                this.sessionId = session.session_id;
                
                // Connect WebSocket
                this.ws = new WebSocket(`ws://localhost:8000/stream/${this.sessionId}`);
                this.ws.onmessage = this.handleMessage.bind(this);
                this.ws.onopen = this.handleOpen.bind(this);
                
                // Start audio recording
                await this.startAudioRecording();
            }

            async startAudioRecording() {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: { 
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true
                    } 
                });
                
                this.mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
                
                this.mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        this.sendAudioChunk(event.data);
                    }
                };
                
                this.mediaRecorder.start(250); // 250ms chunks
            }

            sendAudioChunk(audioBlob) {
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64Audio = reader.result.split(',')[1];
                    this.ws.send(JSON.stringify({
                        type: 'audio',
                        data: {
                            audio: base64Audio,
                            format: 'webm_opus'
                        }
                    }));
                };
                reader.readAsDataURL(audioBlob);
            }

            handleOpen() {
                this.ws.send(JSON.stringify({
                    type: 'session_control',
                    data: { action: 'start' }
                }));
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
            }

            handleMessage(event) {
                const message = JSON.parse(event.data);
                
                switch(message.type) {
                    case 'transcript_final':
                        this.displayTranscript(message.data.text);
                        break;
                    case 'agent_message':
                        this.displayResponse(message.data.message);
                        break;
                    case 'audio_response':
                        this.playAudioResponse(message.data.audio);
                        break;
                    case 'error':
                        this.handleError(message.data);
                        break;
                }
            }

            displayTranscript(text) {
                const transcript = document.getElementById('transcript');
                transcript.innerHTML += `<div><strong>You:</strong> ${text}</div>`;
            }

            displayResponse(text) {
                const response = document.getElementById('response');
                response.innerHTML += `<div><strong>Agent:</strong> ${text}</div>`;
            }

            playAudioResponse(base64Audio) {
                const audioBlob = this.base64ToBlob(base64Audio, 'audio/wav');
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play();
            }

            base64ToBlob(base64, mimeType) {
                const byteCharacters = atob(base64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                return new Blob([byteArray], { type: mimeType });
            }

            handleError(errorData) {
                console.error('Voice Agent Error:', errorData);
                alert(`Error: ${errorData.message}`);
            }

            stopConversation() {
                if (this.mediaRecorder) {
                    this.mediaRecorder.stop();
                }
                
                if (this.ws) {
                    this.ws.send(JSON.stringify({
                        type: 'session_control',
                        data: { action: 'stop' }
                    }));
                    this.ws.close();
                }
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }
        }

        // Initialize client
        const client = new VoiceAgentClient();
        
        document.getElementById('startBtn').onclick = () => client.startConversation();
        document.getElementById('stopBtn').onclick = () => client.stopConversation();
    </script>
</body>
</html>
```

## REST API Usage

### Session Management

```bash
# Create a new session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "customer_service_agent",
    "initial_context": {
      "customer_id": "CUST-12345",
      "priority": "high"
    }
  }'

# Response:
# {
#   "session_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "active",
#   "websocket_url": "ws://localhost:8000/stream/550e8400-e29b-41d4-a716-446655440000"
# }

# Get session status
curl http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440000

# End session
curl -X POST http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440000/end \
  -H "Content-Type: application/json" \
  -d '{"reason": "user_request"}'

# Export session transcript
curl "http://localhost:8000/sessions/550e8400-e29b-41d4-a716-446655440000/export?format=json&redact_sensitive=true"
```

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/health

# Response:
# {
#   "status": "healthy",
#   "services": {
#     "transcription": "available",
#     "tts": "available", 
#     "agent_runtime": "available"
#   }
# }
```

## WebSocket Client Development

### Python Client Example

```python
import asyncio
import json
import websockets
import base64
import wave
import pyaudio
from typing import AsyncGenerator

class VoiceAgentPythonClient:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.websocket = None
        self.audio = pyaudio.PyAudio()
        
    async def create_session(self) -> str:
        """Create a new session via REST API."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"http://localhost:8000/sessions") as response:
                data = await response.json()
                return data["session_id"]
    
    async def connect(self, session_id: str):
        """Connect to WebSocket for the session."""
        self.session_id = session_id
        uri = f"{self.base_url}/stream/{session_id}"
        self.websocket = await websockets.connect(uri)
        
        # Start session
        await self.send_control("start")
        
        # Start message handler
        asyncio.create_task(self.message_handler())
    
    async def send_control(self, action: str):
        """Send session control message."""
        message = {
            "type": "session_control",
            "data": {"action": action}
        }
        await self.websocket.send(json.dumps(message))
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to the server."""
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        message = {
            "type": "audio",
            "data": {
                "audio": base64_audio,
                "format": "pcm_16khz_16bit"
            }
        }
        await self.websocket.send(json.dumps(message))
    
    async def message_handler(self):
        """Handle incoming WebSocket messages."""
        async for message_str in self.websocket:
            message = json.loads(message_str)
            
            if message["type"] == "transcript_final":
                print(f"User said: {message['data']['text']}")
            
            elif message["type"] == "agent_message":
                print(f"Agent: {message['data']['message']}")
            
            elif message["type"] == "audio_response":
                await self.play_audio(message["data"]["audio"])
            
            elif message["type"] == "error":
                print(f"Error: {message['data']['message']}")
    
    async def play_audio(self, base64_audio: str):
        """Play audio response."""
        audio_data = base64.b64decode(base64_audio)
        
        # Play using pyaudio
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            output=True
        )
        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
    
    async def record_and_stream(self, duration: int = 5):
        """Record audio and stream to server."""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print(f"Recording for {duration} seconds...")
        
        for _ in range(0, int(16000 / 1024 * duration)):
            data = stream.read(1024)
            await self.send_audio(data)
            await asyncio.sleep(0.01)  # Small delay
        
        stream.stop_stream()
        stream.close()
    
    async def disconnect(self):
        """Disconnect from the session."""
        if self.websocket:
            await self.send_control("stop")
            await self.websocket.close()

# Usage example
async def main():
    client = VoiceAgentPythonClient()
    
    # Create session
    session_id = await client.create_session()
    print(f"Created session: {session_id}")
    
    # Connect
    await client.connect(session_id)
    
    # Record and send audio
    await client.record_and_stream(duration=5)
    
    # Wait for responses
    await asyncio.sleep(3)
    
    # Disconnect
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Node.js Client Example

```javascript
const WebSocket = require('ws');
const fs = require('fs');
const axios = require('axios');

class VoiceAgentNodeClient {
    constructor(baseUrl = 'ws://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
        this.ws = null;
    }

    async createSession() {
        const response = await axios.post('http://localhost:8000/sessions', {
            agent_type: 'customer_service_agent'
        });
        return response.data.session_id;
    }

    async connect(sessionId) {
        this.sessionId = sessionId;
        this.ws = new WebSocket(`${this.baseUrl}/stream/${sessionId}`);
        
        this.ws.on('open', () => {
            console.log('Connected to voice agent');
            this.sendControl('start');
        });
        
        this.ws.on('message', (data) => {
            const message = JSON.parse(data);
            this.handleMessage(message);
        });
        
        this.ws.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    }

    sendControl(action) {
        const message = {
            type: 'session_control',
            data: { action }
        };
        this.ws.send(JSON.stringify(message));
    }

    sendAudioFile(filePath) {
        const audioData = fs.readFileSync(filePath);
        const base64Audio = audioData.toString('base64');
        
        const message = {
            type: 'audio',
            data: {
                audio: base64Audio,
                format: 'pcm_16khz_16bit'
            }
        };
        this.ws.send(JSON.stringify(message));
    }

    handleMessage(message) {
        switch(message.type) {
            case 'transcript_final':
                console.log(`User said: ${message.data.text}`);
                break;
            case 'agent_message':
                console.log(`Agent: ${message.data.message}`);
                break;
            case 'audio_response':
                this.saveAudioResponse(message.data.audio);
                break;
            case 'error':
                console.error(`Error: ${message.data.message}`);
                break;
        }
    }

    saveAudioResponse(base64Audio) {
        const audioBuffer = Buffer.from(base64Audio, 'base64');
        const fileName = `response_${Date.now()}.wav`;
        fs.writeFileSync(fileName, audioBuffer);
        console.log(`Audio response saved as ${fileName}`);
    }

    disconnect() {
        if (this.ws) {
            this.sendControl('stop');
            this.ws.close();
        }
    }
}

// Usage
async function main() {
    const client = new VoiceAgentNodeClient();
    
    const sessionId = await client.createSession();
    console.log(`Created session: ${sessionId}`);
    
    await client.connect(sessionId);
    
    // Send an audio file
    client.sendAudioFile('./test_audio.wav');
    
    // Wait for responses
    setTimeout(() => {
        client.disconnect();
    }, 10000);
}

main().catch(console.error);
```

## Custom Agent Development

### Creating a Specialized Customer Service Agent

```python
from models.agent import Agent
from typing import Dict, Any, List
import re

class BankingCustomerServiceAgent(Agent):
    """Specialized agent for banking customer service."""
    
    def __init__(self):
        super().__init__(
            name="banking_customer_service_agent",
            purpose="Handle banking customer service inquiries with specialized knowledge",
            allowed_tools=[
                "account_balance_lookup",
                "transaction_history", 
                "card_management",
                "loan_inquiry",
                "fraud_detection"
            ],
            guardrails={
                "max_tokens": 2000,
                "sensitive_data_handling": "strict",
                "escalation_policy": "fraud_or_complex_issues"
            }
        )
        
        # Banking-specific intent patterns
        self.intent_patterns = {
            "balance_inquiry": [
                r"balance",
                r"how much.*account",
                r"account balance"
            ],
            "transaction_history": [
                r"transactions?",
                r"recent.*activity",
                r"statement"
            ],
            "card_issues": [
                r"card.*not.*work",
                r"declined",
                r"lost.*card",
                r"stolen.*card"
            ],
            "loan_inquiry": [
                r"loan",
                r"mortgage",
                r"credit"
            ]
        }
    
    async def process_intent(self, utterance: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process banking-specific intents."""
        
        # Detect intent
        intent = self._detect_intent(utterance)
        
        # Route to appropriate handler
        if intent == "balance_inquiry":
            return await self._handle_balance_inquiry(utterance, context)
        elif intent == "transaction_history":
            return await self._handle_transaction_history(utterance, context)
        elif intent == "card_issues":
            return await self._handle_card_issues(utterance, context)
        elif intent == "loan_inquiry":
            return await self._handle_loan_inquiry(utterance, context)
        else:
            return await self._handle_general_inquiry(utterance, context)
    
    def _detect_intent(self, utterance: str) -> str:
        """Detect user intent from utterance."""
        utterance_lower = utterance.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, utterance_lower):
                    return intent
        
        return "general"
    
    async def _handle_balance_inquiry(self, utterance: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle account balance inquiries."""
        return {
            "response": "I'll help you check your account balance. Let me look that up for you.",
            "tasks": [
                {
                    "description": "Retrieve customer account balance",
                    "tool": "account_balance_lookup",
                    "parameters": {
                        "customer_id": context.get("customer_id"),
                        "account_type": "checking"  # Default to checking
                    }
                }
            ],
            "follow_up_questions": [
                "Would you like to see your recent transactions as well?"
            ]
        }
    
    async def _handle_card_issues(self, utterance: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle card-related issues with security considerations."""
        
        # Check for fraud indicators
        if any(word in utterance.lower() for word in ["stolen", "fraud", "unauthorized"]):
            return {
                "response": "I understand this is a security concern. Let me immediately secure your account and help you with this issue.",
                "tasks": [
                    {
                        "description": "Check for fraudulent activity",
                        "tool": "fraud_detection",
                        "parameters": {
                            "customer_id": context.get("customer_id"),
                            "urgency": "high"
                        }
                    },
                    {
                        "description": "Temporarily block card",
                        "tool": "card_management", 
                        "parameters": {
                            "action": "temporary_block",
                            "customer_id": context.get("customer_id")
                        }
                    }
                ],
                "escalation_required": True,
                "priority": "urgent"
            }
        else:
            return {
                "response": "I can help you with your card issue. Let me check your card status.",
                "tasks": [
                    {
                        "description": "Check card status",
                        "tool": "card_management",
                        "parameters": {
                            "action": "status_check",
                            "customer_id": context.get("customer_id")
                        }
                    }
                ]
            }

# Tool Implementation Example
class AccountBalanceLookupTool:
    """Tool for looking up customer account balances."""
    
    def __init__(self, banking_api_client):
        self.banking_api = banking_api_client
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute account balance lookup."""
        customer_id = parameters.get("customer_id")
        account_type = parameters.get("account_type", "checking")
        
        try:
            # Call banking API
            balance_data = await self.banking_api.get_account_balance(
                customer_id=customer_id,
                account_type=account_type
            )
            
            return {
                "status": "success",
                "data": {
                    "balance": balance_data["balance"],
                    "available_balance": balance_data["available_balance"],
                    "account_type": account_type,
                    "currency": "USD",
                    "last_updated": balance_data["timestamp"]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_code": "BALANCE_LOOKUP_FAILED",
                "message": f"Unable to retrieve balance: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Return tool parameter schema."""
        return {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier"
                },
                "account_type": {
                    "type": "string", 
                    "enum": ["checking", "savings", "credit"],
                    "description": "Type of account to check"
                }
            },
            "required": ["customer_id"]
        }
```

## Phone Integration

### Azure Communication Services Setup

```python
import os
from azure.communication.callautomation import CallAutomationClient
from azure.communication.callautomation.models import PhoneNumberIdentifier

class ACSPhoneIntegration:
    """Integration with Azure Communication Services for phone calls."""
    
    def __init__(self):
        self.connection_string = os.getenv("ACS_CONNECTION_STRING")
        self.client = CallAutomationClient.from_connection_string(
            self.connection_string
        )
        self.callback_url = os.getenv("ACS_CALLBACK_URL")
    
    async def handle_incoming_call(self, event_data: Dict[str, Any]):
        """Handle incoming phone call event."""
        
        call_connection_id = event_data.get("data", {}).get("incomingCallContext")
        caller_number = event_data.get("data", {}).get("from", {}).get("phoneNumber")
        
        # Answer the call
        call_connection = await self.client.answer_call(
            incoming_call_context=call_connection_id,
            callback_url=self.callback_url
        )
        
        # Create voice session
        session_id = await self.create_voice_session(caller_number)
        
        # Start media streaming
        await self.start_media_streaming(call_connection, session_id)
        
        return {
            "call_connection_id": call_connection.call_connection_id,
            "session_id": session_id
        }
    
    async def create_voice_session(self, caller_number: str) -> str:
        """Create a voice session for the phone call."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8000/sessions", json={
                "agent_type": "customer_service_agent",
                "initial_context": {
                    "caller_phone": caller_number,
                    "channel": "phone"
                }
            }) as response:
                data = await response.json()
                return data["session_id"]
    
    async def start_media_streaming(self, call_connection, session_id: str):
        """Start media streaming between ACS and voice agent."""
        
        # Configure media streaming
        media_streaming_options = {
            "transport_url": f"wss://your-app.azurecontainerapps.io/acs/media/{session_id}",
            "transport_type": "websocket",
            "content_type": "audio",
            "audio_channel_type": "unmixed"
        }
        
        await call_connection.start_media_streaming(
            **media_streaming_options
        )
```

### Phone Call Handler

```python
from quart import Quart, request, jsonify
import json

app = Quart(__name__)

@app.route("/acs/incomingcall", methods=["POST"])
async def handle_incoming_call():
    """Handle incoming call webhook from ACS."""
    
    event_data = await request.get_json()
    
    # Validate webhook
    if not event_data or event_data.get("eventType") != "Microsoft.Communication.IncomingCall":
        return jsonify({"error": "Invalid event"}), 400
    
    # Process incoming call
    acs_integration = ACSPhoneIntegration()
    result = await acs_integration.handle_incoming_call(event_data)
    
    return jsonify({
        "status": "accepted",
        "call_connection_id": result["call_connection_id"]
    })

@app.route("/acs/media/<session_id>", websocket=True)
async def handle_media_streaming(session_id: str):
    """Handle media streaming WebSocket from ACS."""
    
    while True:
        # Receive audio from ACS
        audio_data = await websocket.receive()
        
        # Forward to voice agent WebSocket
        voice_agent_ws = get_voice_agent_connection(session_id)
        if voice_agent_ws:
            await voice_agent_ws.send(json.dumps({
                "type": "audio",
                "data": {
                    "audio": audio_data,
                    "format": "pcm_8khz_16bit"  # ACS format
                }
            }))
```

## Production Deployment

### Azure Container Apps Deployment

```yaml
# azure-container-app.yaml
apiVersion: 2023-05-01
type: Microsoft.App/containerApps
properties:
  environmentId: /subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.App/managedEnvironments/{env}
  configuration:
    secrets:
    - name: azure-voice-api-key
      keyVaultUrl: https://{keyvault}.vault.azure.net/secrets/voice-api-key
    - name: acs-connection-string
      keyVaultUrl: https://{keyvault}.vault.azure.net/secrets/acs-connection
    ingress:
      external: true
      targetPort: 8000
      allowInsecure: false
      traffic:
      - weight: 100
        latestRevision: true
  template:
    scale:
      minReplicas: 2
      maxReplicas: 10
      rules:
      - name: http-scaling
        http:
          metadata:
            concurrentRequests: 50
    containers:
    - name: voice-agent
      image: your-registry.azurecr.io/voice-agent:latest
      env:
      - name: AZURE_VOICE_LIVE_API_KEY
        secretRef: azure-voice-api-key
      - name: ACS_CONNECTION_STRING
        secretRef: acs-connection-string
      - name: AZURE_CLIENT_ID
        value: "{managed-identity-client-id}"
      resources:
        cpu: 1.0
        memory: 2Gi
      probes:
      - type: liveness
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 30
        periodSeconds: 10
      - type: readiness
        httpGet:
          path: /health
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 5
```

### Environment Configuration

```bash
# production.env
AZURE_VOICE_LIVE_API_KEY=<from-key-vault>
AZURE_VOICE_LIVE_ENDPOINT=https://eastus.api.cognitive.microsoft.com/
ACS_CONNECTION_STRING=<from-key-vault>
AZURE_CLIENT_ID=<managed-identity-client-id>

# Performance tuning
MAX_SESSION_DURATION=3600
CONTEXT_WINDOW_SIZE=50
CONCURRENT_SESSION_LIMIT=100

# Logging and monitoring
LOG_LEVEL=INFO
APPLICATIONINSIGHTS_CONNECTION_STRING=<app-insights-connection>

# Security
ALLOWED_ORIGINS=https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60
```

### Monitoring and Alerting

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace, metrics
import logging

# Configure Azure Monitor
configure_azure_monitor(
    connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
)

# Set up custom metrics
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom metrics
session_counter = meter.create_counter(
    "voice_agent_sessions_total",
    description="Total number of voice sessions created"
)

transcription_duration = meter.create_histogram(
    "voice_agent_transcription_duration_seconds",
    description="Duration of transcription operations"
)

agent_response_duration = meter.create_histogram(
    "voice_agent_response_duration_seconds", 
    description="Duration of agent response generation"
)

# Usage in application
@tracer.start_as_current_span("create_session")
async def create_session():
    session_counter.add(1)
    # ... session creation logic
    
@tracer.start_as_current_span("transcribe_audio")
async def transcribe_audio(audio_data):
    start_time = time.time()
    try:
        result = await transcription_service.transcribe(audio_data)
        return result
    finally:
        duration = time.time() - start_time
        transcription_duration.record(duration)
```

This comprehensive set of examples covers the major use cases and integration patterns for the Voice Agent system. Each example includes error handling, proper resource management, and production-ready patterns.