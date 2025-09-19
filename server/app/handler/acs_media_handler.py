"""Handles media streaming to Azure Voice Live API via WebSocket."""

import asyncio
import base64
import json
import logging
import uuid
import os

from azure.identity.aio import ManagedIdentityCredential
from websockets.asyncio.client import connect as ws_connect
from websockets.typing import Data
from app.orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)
conversation_logger = logging.getLogger("conversation")


def session_config():
    """Returns the default session configuration for Voice Live."""
    return {
        "type": "session.update",
        "session": {
            "instructions": "You are a helpful AI assistant responding in natural, engaging language.",
            "turn_detection": {
                "type": "azure_semantic_vad",
                "threshold": 0.3,
                "prefix_padding_ms": 200,
                "silence_duration_ms": 200,
                "remove_filler_words": False,
                "end_of_utterance_detection": {
                    "model": "semantic_detection_v1",
                    "threshold": 0.01,
                    "timeout": 2,
                },
            },
            "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
            "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
            "voice": {
                "name": "en-US-Aria:DragonHDLatestNeural",
                "type": "azure-standard",
                "temperature": 0.8,
            },
        },
    }


class ACSMediaHandler:
    """Manages audio streaming between client and Azure Voice Live API."""

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
        self.conv_history: list[dict] = []  # {role: user|agent, content: str}
        self.last_agent: str | None = None
        self._awaiting_response: dict[str, float] = {}  # agent -> start time
        self._turn_completed = False
        self.log_event_types = os.getenv("LOG_EVENT_TYPES", "0") == "1"

    def _generate_guid(self):
        return str(uuid.uuid4())

    async def connect(self):
        """Connects to Azure Voice Live API via WebSocket."""
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
        await self._send_json({"type": "response.create"})

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
        """Handles incoming events from the Voice Live WebSocket."""
        try:
            if self.ws is None:
                logger.error("[VoiceLiveACSHandler] WebSocket is not connected.")
                return
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")
                if self.log_event_types:
                    logger.info("[EVT] %s", event_type)

                match event_type:
                    case "session.created":
                        session_id = event.get("session", {}).get("id")
                        logger.info("[VoiceLiveACSHandler] Session ID: %s", session_id)

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
                        transcript = event.get("transcript")
                        self.conv_history.append({"role": "user", "content": transcript})
                        orch = Orchestrator(session_id=self._generate_guid(), user_id="local-user", context={})
                        agent = orch.classify(transcript)
                        self.last_agent = agent
                        instructions = orch.build_agent_instructions(agent, transcript, self.conv_history)
                        conversation_logger.info("ROUTED_AGENT: %s", agent)
                        logger.info("ROUTED_AGENT: %s", agent)  # duplicate to root for terminal visibility
                        # Request dynamic generation from Voice Live using instructions as system prompt for this turn
                        await self._send_json({
                            "type": "response.create",
                            "response": {
                                "modalities": ["audio"],
                                "instructions": instructions,
                            },
                        })
                        self._turn_completed = False
                        # Start watchdog for response
                        asyncio.create_task(self._response_watchdog(agent))
                        
                    case "conversation.item.input_audio_transcription.failed":
                        error_msg = event.get("error")
                        logger.warning("Transcription Error: %s", error_msg)

                    case "response.done":
                        response = event.get("response", {})
                        logger.info("Response Done: Id=%s", response.get("id"))
                        if response.get("status_details"):
                            logger.info(
                                "Status Details: %s",
                                json.dumps(response["status_details"], indent=2),
                            )

                    case "response.audio_transcript.done":
                        transcript = event.get("transcript")
                        agent = self.last_agent or "Agent"
                        logger.info("AI (%s): %s", agent, transcript)
                        conversation_logger.info("%s RESPONSE: %s", agent, transcript)
                        logger.info("%s RESPONSE: %s", agent, transcript)  # duplicate to root for terminal visibility
                        for h in conversation_logger.handlers:
                            try:
                                h.flush()
                            except Exception:
                                pass
                        self.conv_history.append({"role": agent, "content": transcript})
                        self._turn_completed = True
                        await self.send_message(json.dumps({"Kind": "Transcription", "Text": f"{agent}: {transcript}"}))

                    case "response.audio.delta":
                        delta = event.get("delta")
                        if self.is_raw_audio:
                            audio_bytes = base64.b64decode(delta)
                            await self.send_message(audio_bytes)
                        else:
                            await self.voicelive_to_acs(delta)

                    case "response.audio_transcript.delta":
                        # Ignore partial transcripts for minimal logging mode
                        pass

                    case "error":
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
            if self.incoming_websocket is not None:
                await self.incoming_websocket.send(message)
            else:
                logger.error("[VoiceLiveACSHandler] incoming_websocket is None, cannot send message")
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

    async def _response_watchdog(self, agent: str, timeout: float = 10.0):
        """Logs a timeout if no final transcript event arrives within timeout seconds."""
        try:
            await asyncio.sleep(timeout)
            if not self._turn_completed and self.last_agent == agent:
                msg = f"RESPONSE_TIMEOUT: {agent} (no final transcript within {timeout}s)"
                logger.warning(msg)
                conversation_logger.info(msg)
        except Exception:  # safeguard so watchdog never crashes main loop
            logger.exception("Watchdog error")

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
