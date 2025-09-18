import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path
from datetime import datetime
import uuid


@pytest.fixture
def agent_message_schema():
    """Load the agent message schema from the contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-what-a-voice" / "contracts" / "agent-message.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_valid_agent_message_schema(agent_message_schema):
    """Test that a valid agent message object passes schema validation."""
    valid_message = {
        "id": str(uuid.uuid4()),
        "agent": "planner",
        "type": "plan",
        "timestamp": datetime.now().isoformat()
    }
    
    # Should not raise ValidationError
    validate(instance=valid_message, schema=agent_message_schema)


def test_valid_agent_message_with_payload(agent_message_schema):
    """Test that a valid agent message with payload passes schema validation."""
    valid_message = {
        "id": str(uuid.uuid4()),
        "agent": "executor",
        "type": "action",
        "timestamp": datetime.now().isoformat(),
        "payload": {
            "action": "send_email",
            "parameters": {
                "to": "user@example.com",
                "subject": "Test email"
            }
        }
    }
    
    # Should not raise ValidationError
    validate(instance=valid_message, schema=agent_message_schema)


def test_agent_message_missing_required_field(agent_message_schema):
    """Test that agent message missing required fields fails validation."""
    invalid_message = {
        "id": str(uuid.uuid4()),
        "agent": "planner",
        "type": "plan"
        # Missing timestamp
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_message, schema=agent_message_schema)


def test_agent_message_invalid_type(agent_message_schema):
    """Test that agent message with invalid type fails validation."""
    invalid_message = {
        "id": str(uuid.uuid4()),
        "agent": "planner",
        "type": "invalid_type",
        "timestamp": datetime.now().isoformat()
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_message, schema=agent_message_schema)


def test_agent_message_valid_types(agent_message_schema):
    """Test that all valid message types pass validation."""
    valid_types = ["plan", "action", "observation", "response", "error"]
    
    for msg_type in valid_types:
        valid_message = {
            "id": str(uuid.uuid4()),
            "agent": "test_agent",
            "type": msg_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Should not raise ValidationError
        validate(instance=valid_message, schema=agent_message_schema)


def test_agent_message_null_payload(agent_message_schema):
    """Test that agent message with null payload passes validation."""
    valid_message = {
        "id": str(uuid.uuid4()),
        "agent": "observer",
        "type": "observation",
        "timestamp": datetime.now().isoformat(),
        "payload": None
    }
    
    # Should not raise ValidationError
    validate(instance=valid_message, schema=agent_message_schema)


def test_agent_message_additional_properties(agent_message_schema):
    """Test that agent message with additional properties fails validation."""
    invalid_message = {
        "id": str(uuid.uuid4()),
        "agent": "planner",
        "type": "plan",
        "timestamp": datetime.now().isoformat(),
        "extra_field": "not allowed"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_message, schema=agent_message_schema)