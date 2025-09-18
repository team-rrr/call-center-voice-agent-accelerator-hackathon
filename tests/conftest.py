import asyncio
import pytest
from quart import Quart
from quart.testing import QuartClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def app():
    """Create a test instance of the Quart app."""
    app = Quart(__name__)
    app.config.update({
        "TESTING": True,
        "ACS_CONNECTION_STRING": "test_connection_string",
        "AZURE_VOICE_LIVE_API_KEY": "test_api_key",
        "AZURE_VOICE_LIVE_ENDPOINT": "https://test.endpoint.com",
        "VOICE_LIVE_MODEL": "gpt-4o-mini",
        "TTS_VOICE": "en-US-JennyNeural"
    })
    return app


@pytest.fixture
async def client(app):
    """Create a test client for the Quart app."""
    return app.test_client()