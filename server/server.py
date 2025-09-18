import asyncio
import logging
import os

from app.handler.acs_event_handler import AcsEventHandler
from app.handler.acs_media_handler import ACSMediaHandler
from handler.stream_handler import StreamHandler
from services.session_store import SessionStore
from services.agent_runtime import AgentRuntime
from services.transcription import TranscriptionService
from services.tts import TTSService
from services.error_events import ErrorEventService
from dotenv import load_dotenv
from quart import Quart, request, websocket, jsonify

load_dotenv()

app = Quart(__name__)
app.config["AZURE_VOICE_LIVE_API_KEY"] = os.getenv("AZURE_VOICE_LIVE_API_KEY", "")
app.config["AZURE_VOICE_LIVE_ENDPOINT"] = os.getenv("AZURE_VOICE_LIVE_ENDPOINT")
app.config["VOICE_LIVE_MODEL"] = os.getenv("VOICE_LIVE_MODEL", "gpt-4o-mini")
app.config["ACS_CONNECTION_STRING"] = os.getenv("ACS_CONNECTION_STRING")
app.config["ACS_DEV_TUNNEL"] = os.getenv("ACS_DEV_TUNNEL", "")
app.config["AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID"] = os.getenv(
    "AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID", ""
)
app.config["TTS_VOICE"] = os.getenv("TTS_VOICE", "en-US-JennyNeural")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)

# Initialize existing ACS handler
acs_handler = AcsEventHandler(app.config)

# Initialize new services for voice agent MVP
session_store = SessionStore()
agent_runtime = AgentRuntime()
transcription_service = TranscriptionService()
tts_service = TTSService(voice=app.config["TTS_VOICE"])
error_service = ErrorEventService()

# Initialize stream handler
stream_handler = StreamHandler(
    session_store=session_store,
    agent_runtime=agent_runtime,
    transcription_service=transcription_service,
    tts_service=tts_service,
    error_service=error_service
)


# Health endpoint
@app.route("/health")
async def health():
    """Health check endpoint."""
    try:
        # Get service statuses
        session_counts = await session_store.get_session_count()
        agent_status = agent_runtime.get_runtime_status()
        transcription_status = await transcription_service.get_service_status()
        tts_status = await tts_service.get_service_status()
        error_stats = error_service.get_error_stats()
        
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "ready": True,
            "services": {
                "sessions": session_counts,
                "agent_runtime": agent_status,
                "transcription": transcription_status,
                "tts": tts_status,
                "errors": error_stats
            },
            "timestamp": "2025-09-18T12:00:00Z"
        })
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "version": "1.0.0", 
            "ready": False,
            "error": str(e),
            "timestamp": "2025-09-18T12:00:00Z"
        }), 500


# Session management endpoints
@app.route("/sessions", methods=["POST"])
async def create_session():
    """Create a new voice session."""
    try:
        session = await session_store.create_session()
        return jsonify({
            "session_id": session.id,
            "status": "created",
            "start_time": session.start_time.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Failed to create session: {str(e)}")
        return jsonify({
            "error": "Failed to create session",
            "details": str(e)
        }), 500


@app.route("/sessions/<session_id>", methods=["GET"])
async def get_session(session_id: str):
    """Get session information."""
    try:
        session = await session_store.get_session(session_id)
        
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Get context summary
        context_summary = agent_runtime.get_session_context_summary(session_id)
        
        return jsonify({
            "session": {
                "id": session.id,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "version": session.version,
                "duration": session.duration()
            },
            "context": context_summary
        })
        
    except Exception as e:
        logging.error(f"Failed to get session {session_id}: {str(e)}")
        return jsonify({
            "error": "Failed to get session",
            "details": str(e)
        }), 500


# Voice streaming WebSocket endpoint
@app.websocket("/ws")
async def voice_stream():
    """WebSocket endpoint for voice streaming interactions."""
    logger = logging.getLogger("voice_stream")
    logger.info("New voice streaming WebSocket connection")
    
    try:
        await stream_handler.handle_websocket_connection()
    except Exception as e:
        logger.error(f"Voice stream error: {str(e)}")


# Existing ACS endpoints (preserved)
@app.route("/acs/incomingcall", methods=["POST"])
async def incoming_call_handler():
    """Handles initial incoming call event from EventGrid."""
    events = await request.get_json()
    host_url = request.host_url.replace("http://", "https://", 1).rstrip("/")
    return await acs_handler.process_incoming_call(events, host_url, app.config)


@app.route("/acs/callbacks/<context_id>", methods=["POST"])
async def acs_event_callbacks(context_id):
    """Handles ACS event callbacks for call connection and streaming events."""
    raw_events = await request.get_json()
    return await acs_handler.process_callback_events(context_id, raw_events, app.config)


@app.websocket("/acs/ws")
async def acs_ws():
    """WebSocket endpoint for ACS to send audio to Voice Live."""
    logger = logging.getLogger("acs_ws")
    logger.info("Incoming ACS WebSocket connection")
    handler = ACSMediaHandler(app.config)
    await handler.init_incoming_websocket(websocket, is_raw_audio=False)
    asyncio.create_task(handler.connect())
    try:
        while True:
            msg = await websocket.receive()
            await handler.acs_to_voicelive(msg)
    except Exception:
        logger.exception("ACS WebSocket connection closed")


@app.websocket("/web/ws")
async def web_ws():
    """WebSocket endpoint for web clients to send audio to Voice Live."""
    logger = logging.getLogger("web_ws")
    logger.info("Incoming Web WebSocket connection")
    handler = ACSMediaHandler(app.config)
    await handler.init_incoming_websocket(websocket, is_raw_audio=True)
    asyncio.create_task(handler.connect())
    try:
        while True:
            msg = await websocket.receive()
            await handler.web_to_voicelive(msg)
    except Exception:
        logger.exception("Web WebSocket connection closed")


@app.route("/")
async def index():
    """Serves the static index page."""
    return await app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
