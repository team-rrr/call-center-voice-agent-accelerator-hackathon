"""Handles media streaming to Azure Voice Live API via WebSocket."""

import asyncio
import base64
import json
import logging
import uuid
from typing import Optional

from azure.identity.aio import ManagedIdentityCredential
from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data

# Import orchestrator for voice integration (Phase 2G-1)
from app.backend.services.simple_orchestrator import get_orchestrator_service

logger = logging.getLogger(__name__)


def session_config():
    """Returns the session configuration for Voice Live with orchestrator integration."""
    return {
        "type": "session.update",
        "session": {
            "instructions": "Healthcare appointment preparation assistant with multi-agent orchestrator integration.",
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.3,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 500,  # Slightly longer for healthcare conversations
                "remove_filler_words": False,
                "end_of_utterance_detection": {
                    "model": "semantic_detection_v1",
                    "threshold": 0.01,
                    "timeout": 3,  # Longer timeout for thoughtful responses
                },
            },
            "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
            "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
            "voice": {
                "name": "en-US-Aria:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.7,  # Slightly more controlled for healthcare
            },
            # Phase 2G-1: Configure for manual response mode
            "modalities": ["text", "audio"],
            "input_audio_transcription": {
                "model": "whisper-1"
            }
        },
    }


class ACSMediaHandler:
    """Manages audio streaming between client and Azure Voice Live API with orchestrator integration."""

    def __init__(self, config):
        self.endpoint = config["AZURE_VOICE_LIVE_ENDPOINT"]
        self.model = config["VOICE_LIVE_MODEL"]
        self.api_key = config["AZURE_VOICE_LIVE_API_KEY"]
        self.client_id = config["AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID"]
        self.send_queue = asyncio.Queue()
        self.ws = None
        self.send_task = None
        self.incoming_websocket = None
        self.is_raw_audio = True
        
        # Phase 2G-1: Orchestrator integration fields
        self.orchestrator_service = None
        self.use_orchestrator = True  # Flag to enable/disable orchestrator
        self.session_id = None
        self.conversation_history = []
        self.response_in_progress = False  # Track active responses

    def _generate_guid(self):
        return str(uuid.uuid4())
    
    async def initialize_orchestrator(self):
        """Initialize the orchestrator service for voice integration."""
        try:
            self.orchestrator_service = await get_orchestrator_service()
            if self.orchestrator_service:
                logger.info("[VoiceLiveACSHandler] Orchestrator service initialized successfully")
                return True
            else:
                logger.warning("[VoiceLiveACSHandler] Failed to initialize orchestrator service")
                self.use_orchestrator = False
                return False
        except Exception as e:
            logger.error(f"[VoiceLiveACSHandler] Error initializing orchestrator: {e}")
            self.use_orchestrator = False
            return False

    async def connect(self):
        """Connects to Azure Voice Live API via WebSocket and initializes orchestrator."""
        # Phase 2G-1: Initialize orchestrator service first
        await self.initialize_orchestrator()
        
        url = f"{self.endpoint}/voice-live/realtime?api-version=2025-05-01-preview&model={self.model}"
        url = url.replace("https://", "wss://")

        headers = {"x-ms-client-request-id": self._generate_guid()}

        if self.client_id:
            credential = ManagedIdentityCredential(
                managed_identity_client_id=self.client_id
            )
            token = await credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            )
            headers["Authorization"] = f"Bearer {token.token}"
        else:
            headers["api-key"] = self.api_key

        self.ws = await ws_connect(url, additional_headers=headers)
        logger.info("[VoiceLiveACSHandler] Connected to Voice Live API")

        await self._send_json(session_config())
        
        # Phase 2G-1: Don't auto-create response - let orchestrator handle it
        # await self._send_json({"type": "response.create"})

        asyncio.create_task(self._receiver_loop())
        self.send_task = asyncio.create_task(self._sender_loop())

    async def init_incoming_websocket(self, socket, is_raw_audio=True):
        """Sets up incoming ACS WebSocket."""
        self.incoming_websocket = socket
        self.is_raw_audio = is_raw_audio

    async def audio_to_voicelive(self, audio_b64: str):
        """Queues audio data to be sent to Voice Live API."""
        await self.send_queue.put(
            json.dumps({"type": "input_audio_buffer.append", "audio": audio_b64})
        )

    async def _send_json(self, obj):
        """Sends a JSON object over WebSocket."""
        if self.ws:
            await self.ws.send(json.dumps(obj))

    async def _generate_orchestrator_response(self, user_message: str) -> Optional[str]:
        """Generate response using the multi-agent orchestrator."""
        if not self.use_orchestrator or not self.orchestrator_service:
            logger.warning("[VoiceLiveACSHandler] Orchestrator not available, using fallback")
            return "I'm sorry, I'm having trouble accessing my healthcare knowledge system right now. Please try again."
        
        try:
            logger.info(f"[VoiceLiveACSHandler] Sending to orchestrator: {user_message}")
            
            # Call the orchestrator service with the correct method name
            session_id = self.session_id or "voice_session_" + self._generate_guid()
            response = await self.orchestrator_service.call_orchestrator(user_message, session_id)
            
            if response and "response" in response:
                orchestrator_text = response["response"]
                logger.info(f"[VoiceLiveACSHandler] Orchestrator response: {orchestrator_text[:100]}...")
                
                # Track conversation history
                self.conversation_history.append({
                    "user": user_message,
                    "assistant": orchestrator_text,
                    "timestamp": asyncio.get_event_loop().time()
                })
                
                return orchestrator_text
            else:
                logger.warning("[VoiceLiveACSHandler] Invalid orchestrator response format")
                return "I apologize, but I'm having trouble processing your request right now. Could you please try asking again?"
                
        except Exception as e:
            logger.error(f"[VoiceLiveACSHandler] Error generating orchestrator response: {e}")
            return "I'm experiencing some technical difficulties. Please try your question again in a moment."
    
    async def _send_orchestrator_response(self, response_text: str):
        """Send orchestrator response through Voice Live TTS."""
        if self.response_in_progress:
            logger.warning("[VoiceLiveACSHandler] Response already in progress, skipping")
            return
            
        try:
            self.response_in_progress = True
            
            # First, cancel any existing response to prevent conflicts
            await self._send_json({"type": "response.cancel"})
            
            # Small delay to ensure cancellation is processed
            await asyncio.sleep(0.1)
            
            # Create a conversation item with the orchestrator response
            conversation_item = {
                "type": "conversation.item.create",
                "item": {
                    "id": self._generate_guid(),
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ]
                }
            }
            
            await self._send_json(conversation_item)
            
            # Create response to trigger TTS
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Please convert the assistant message to speech using a warm, caring tone appropriate for healthcare guidance."
                }
            }
            
            await self._send_json(response_create)
            logger.info("[VoiceLiveACSHandler] Sent orchestrator response for TTS conversion")
            
        except Exception as e:
            logger.error(f"[VoiceLiveACSHandler] Error sending orchestrator response: {e}")
            self.response_in_progress = False

    async def _sender_loop(self):
        """Continuously sends messages from the queue to the Voice Live WebSocket."""
        try:
            while True:
                msg = await self.send_queue.get()
                if self.ws:
                    await self.ws.send(msg)
        except Exception:
            logger.exception("[VoiceLiveACSHandler] Sender loop error")

    async def _receiver_loop(self):
        """Handles incoming events from the Voice Live WebSocket with orchestrator integration."""
        try:
            if not self.ws:
                logger.error("[VoiceLiveACSHandler] WebSocket connection not established")
                return
                
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                match event_type:
                    case "session.created":
                        self.session_id = event.get("session", {}).get("id")
                        logger.info("[VoiceLiveACSHandler] Session ID: %s", self.session_id)

                    case "input_audio_buffer.cleared":
                        logger.info("Input Audio Buffer Cleared Message")

                    case "input_audio_buffer.speech_started":
                        logger.info(
                            "Voice activity detection started at %s ms",
                            event.get("audio_start_ms"),
                        )
                        await self.stop_audio()

                    case "input_audio_buffer.speech_stopped":
                        logger.info("Speech stopped")

                    case "conversation.item.input_audio_transcription.completed":
                        # Phase 2G-1: This is where we intercept user input and route to orchestrator
                        transcript = event.get("transcript")
                        logger.info("User: %s", transcript)
                        
                        if transcript and transcript.strip() and not self.response_in_progress:
                            # Generate response using orchestrator instead of Voice Live AI
                            orchestrator_response = await self._generate_orchestrator_response(transcript)
                            if orchestrator_response:
                                await self._send_orchestrator_response(orchestrator_response)

                    case "conversation.item.input_audio_transcription.failed":
                        error_msg = event.get("error")
                        logger.warning("Transcription Error: %s", error_msg)

                    case "response.done":
                        response = event.get("response", {})
                        logger.info("Response Done: Id=%s", response.get("id"))
                        self.response_in_progress = False  # Reset response flag
                        if response.get("status_details"):
                            logger.info(
                                "Status Details: %s",
                                json.dumps(response["status_details"], indent=2),
                            )

                    case "response.audio_transcript.done":
                        transcript = event.get("transcript")
                        logger.info("AI: %s", transcript)
                        await self.send_message(
                            json.dumps({"Kind": "Transcription", "Text": transcript})
                        )

                    case "response.audio.delta":
                        delta = event.get("delta")
                        if self.is_raw_audio:
                            audio_bytes = base64.b64decode(delta)
                            await self.send_message(audio_bytes)
                        else:
                            await self.voicelive_to_acs(delta)

                    case "error":
                        error_details = event.get("error", {})
                        error_code = error_details.get("code")
                        
                        if error_code == "conversation_already_has_active_response":
                            logger.warning("[VoiceLiveACSHandler] Conversation busy - will retry on next user input")
                            self.response_in_progress = False  # Reset flag to allow retry
                        else:
                            logger.error("Voice Live Error: %s", event)

                    case _:
                        logger.debug(
                            "[VoiceLiveACSHandler] Other event: %s", event_type
                        )
        except Exception:
            logger.exception("[VoiceLiveACSHandler] Receiver loop error")

    async def send_message(self, message: Data):
        """Sends data back to client WebSocket."""
        try:
            if self.incoming_websocket:
                await self.incoming_websocket.send(message)
            else:
                logger.warning("[VoiceLiveACSHandler] No incoming WebSocket to send message to")
        except Exception:
            logger.exception("[VoiceLiveACSHandler] Failed to send message")

    async def voicelive_to_acs(self, base64_data):
        """Converts Voice Live audio delta to ACS audio message."""
        try:
            data = {
                "Kind": "AudioData",
                "AudioData": {"Data": base64_data},
                "StopAudio": None,
            }
            await self.send_message(json.dumps(data))
        except Exception:
            logger.exception("[VoiceLiveACSHandler] Error in voicelive_to_acs")

    async def stop_audio(self):
        """Sends a StopAudio signal to ACS."""
        stop_audio_data = {"Kind": "StopAudio", "AudioData": None, "StopAudio": {}}
        await self.send_message(json.dumps(stop_audio_data))

    async def acs_to_voicelive(self, stream_data):
        """Processes audio from ACS and forwards to Voice Live if not silent."""
        try:
            data = json.loads(stream_data)
            if data.get("kind") == "AudioData":
                audio_data = data.get("audioData", {})
                if not audio_data.get("silent", True):
                    await self.audio_to_voicelive(audio_data.get("data"))
        except Exception:
            logger.exception("[VoiceLiveACSHandler] Error processing ACS audio")

    async def web_to_voicelive(self, audio_bytes):
        """Encodes raw audio bytes and sends to Voice Live API."""
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await self.audio_to_voicelive(audio_b64)
