import json
import pytest
from jsonschema import validate, ValidationError, FormatChecker
from pathlib import Path
from datetime import datetime
import uuid


@pytest.fixture
def session_schema():
    """Load the session schema from the contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-what-a-voice" / "contracts" / "session.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_valid_session_schema(session_schema):
    """Test that a valid session object passes schema validation."""
    valid_session = {
        "id": str(uuid.uuid4()),
        "status": "active",
        "start_time": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Should not raise ValidationError
    validate(instance=valid_session, schema=session_schema, format_checker=FormatChecker())


def test_valid_session_with_end_time(session_schema):
    """Test that a valid session with end_time passes schema validation."""
    valid_session = {
        "id": str(uuid.uuid4()),
        "status": "ended",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Should not raise ValidationError
    validate(instance=valid_session, schema=session_schema, format_checker=FormatChecker())


def test_session_missing_required_field(session_schema):
    """Test that session missing required fields fails validation."""
    invalid_session = {
        "id": str(uuid.uuid4()),
        "status": "active"
        # Missing start_time and version
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_session, schema=session_schema, format_checker=FormatChecker())


def test_session_invalid_status(session_schema):
    """Test that session with invalid status fails validation."""
    invalid_session = {
        "id": str(uuid.uuid4()),
        "status": "invalid_status",
        "start_time": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_session, schema=session_schema, format_checker=FormatChecker())


def test_session_invalid_uuid(session_schema):
    """Test that session with invalid UUID fails validation."""
    invalid_session = {
        "id": "not-a-uuid",
        "status": "active",
        "start_time": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_session, schema=session_schema, format_checker=FormatChecker())


def test_session_additional_properties(session_schema):
    """Test that session with additional properties fails validation."""
    invalid_session = {
        "id": str(uuid.uuid4()),
        "status": "active",
        "start_time": datetime.now().isoformat(),
        "version": "1.0.0",
        "extra_field": "not allowed"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_session, schema=session_schema, format_checker=FormatChecker())
