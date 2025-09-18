import pytest
import pytest_asyncio
import uuid
from quart import Quart


@pytest_asyncio.fixture
async def test_app():
    """Create a test Quart app with health endpoint."""
    app = Quart(__name__)
    
    @app.route("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0", "ready": True}
    
    @app.route("/sessions", methods=["POST"])
    async def create_session():
        session_id = str(uuid.uuid4())
        return {"session_id": session_id, "status": "created"}
    
    return app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health endpoint returns expected response."""
    app = Quart(__name__)
    
    @app.route("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0", "ready": True}
    
    async with app.test_client() as client:
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = await response.get_json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "ready" in data


@pytest.mark.asyncio
async def test_create_session():
    """Test session creation endpoint."""
    app = Quart(__name__)
    
    @app.route("/sessions", methods=["POST"])
    async def create_session():
        session_id = str(uuid.uuid4())
        return {"session_id": session_id, "status": "created"}
    
    async with app.test_client() as client:
        response = await client.post("/sessions")
        assert response.status_code == 200
        
        data = await response.get_json()
        assert "session_id" in data
        assert data["status"] == "created"
        
        # Verify session_id is a valid UUID
        uuid.UUID(data["session_id"])  # This will raise ValueError if invalid


@pytest.mark.asyncio
async def test_session_start_flow(test_app):
    """Test the complete session start flow."""
    async with test_app.test_client() as client:
        # First check health
        health_response = await client.get("/health")
        assert health_response.status_code == 200
        
        # Then create session
        session_response = await client.post("/sessions")
        assert session_response.status_code == 200
        
        session_data = await session_response.get_json()
        assert session_data["status"] == "created"