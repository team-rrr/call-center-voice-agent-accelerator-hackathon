import asyncio
import logging
import os

from app.handler.acs_event_handler import AcsEventHandler
from app.handler.acs_media_handler import ACSMediaHandler
from dotenv import load_dotenv
from quart import Quart, request, websocket, jsonify
from app.orchestrator.orchestrator import Orchestrator
from app.kernel_agents.agent_factory import AgentFactory

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    force=True,  # override any prior config if a reloader or prior imports set logging
)

# Dedicated conversation logger (separate namespace for filtering/formatting)
conversation_logger = logging.getLogger("conversation")
conversation_logger.setLevel(logging.INFO)
stream_exists = any(isinstance(h, logging.StreamHandler) for h in conversation_logger.handlers)
if not stream_exists:
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(asctime)s | CONVO | %(message)s"))
    conversation_logger.addHandler(sh)
file_exists = any(isinstance(h, logging.FileHandler) for h in conversation_logger.handlers)
if not file_exists:
    fh = logging.FileHandler("conversation.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | CONVO | %(message)s"))
    conversation_logger.addHandler(fh)
conversation_logger.propagate = True
conversation_logger.info("Conversation logger initialized (force config)")

acs_handler = AcsEventHandler(app.config)


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

@app.route("/debug/convo")
async def debug_convo():
    conversation_logger.info("/debug/convo hit test message")
    logging.getLogger(__name__).info("Standard logger also hit /debug/convo")
    return {"status": "ok"}

@app.route("/debug/force-log")
async def debug_force_log():
    root = logging.getLogger()
    info = {
        "root_level": root.level,
        "root_handlers": [type(h).__name__ for h in root.handlers],
        "conversation_handlers": [type(h).__name__ for h in conversation_logger.handlers],
    }
    conversation_logger.info("FORCE TEST root_handlers=%s convo_handlers=%s", info["root_handlers"], info["conversation_handlers"])
    return info

@app.route("/voice-call", methods=["POST"])
async def voice_call():
    data = await request.get_json()
    user_input = data.get("message")
    session_id = data.get("session_id")
    user_id = data.get("user_id")
    context = {}  # Load context as needed

    orchestrator = Orchestrator(session_id, user_id, context)
    response = await orchestrator.handle_voice_call(user_input)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
