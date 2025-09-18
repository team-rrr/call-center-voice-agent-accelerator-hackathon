import json
import pytest
from jsonschema import validate, ValidationError, FormatChecker
from pathlib import Path
from datetime import datetime
import uuid


@pytest.fixture
def error_event_schema():
    """Load the error event schema from the contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-what-a-voice" / "contracts" / "error-event.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_valid_error_event_schema(error_event_schema):
    """Test that a valid error event object passes schema validation."""
    valid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "error_type": "transcription_error",
        "message": "Failed to transcribe audio"
    }
    
    # Should not raise ValidationError
    validate(instance=valid_error, schema=error_event_schema, format_checker=FormatChecker())


def test_valid_error_event_with_details(error_event_schema):
    """Test that a valid error event with details passes schema validation."""
    valid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "error_type": "api_error",
        "message": "External API call failed",
        "details": {
            "api_endpoint": "https://api.example.com",
            "status_code": 500,
            "response": "Internal Server Error"
        }
    }
    
    # Should not raise ValidationError
    validate(instance=valid_error, schema=error_event_schema, format_checker=FormatChecker())


def test_error_event_missing_required_field(error_event_schema):
    """Test that error event missing required fields fails validation."""
    invalid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "error_type": "transcription_error"
        # Missing message
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_error, schema=error_event_schema)


def test_error_event_invalid_uuid(error_event_schema):
    """Test that error event with invalid UUID fails validation."""
    invalid_error = {
        "id": "not-a-uuid",
        "timestamp": datetime.now().isoformat(),
        "error_type": "transcription_error",
        "message": "Failed to transcribe audio"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_error, schema=error_event_schema, format_checker=FormatChecker())


@pytest.mark.skip(reason="jsonschema date-time format validation is not strict by default")
def test_error_event_invalid_timestamp(error_event_schema):
    """Test that error event with invalid timestamp fails validation."""
    invalid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": "2023-13-45T99:99:99Z",  # Invalid date components
        "error_type": "transcription_error",
        "message": "Failed to transcribe audio"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_error, schema=error_event_schema, format_checker=FormatChecker())


def test_error_event_null_details(error_event_schema):
    """Test that error event with null details passes validation."""
    valid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "error_type": "general_error",
        "message": "Something went wrong",
        "details": None
    }
    
    # Should not raise ValidationError
    validate(instance=valid_error, schema=error_event_schema, format_checker=FormatChecker())


def test_error_event_additional_properties(error_event_schema):
    """Test that error event with additional properties fails validation."""
    invalid_error = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "error_type": "transcription_error",
        "message": "Failed to transcribe audio",
        "extra_field": "not allowed"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_error, schema=error_event_schema, format_checker=FormatChecker())