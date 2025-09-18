import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path
from datetime import datetime
import uuid


@pytest.fixture
def utterance_schema():
    """Load the utterance schema from the contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-what-a-voice" / "contracts" / "utterance.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_valid_utterance_schema(utterance_schema):
    """Test that a valid utterance object passes schema validation."""
    valid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello world",
        "confidence": 0.95,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
    
    # Should not raise ValidationError
    validate(instance=valid_utterance, schema=utterance_schema)


def test_valid_utterance_with_interrupted(utterance_schema):
    """Test that a valid utterance with interrupted flag passes schema validation."""
    valid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello wor-",
        "confidence": 0.8,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "interrupted": True
    }
    
    # Should not raise ValidationError
    validate(instance=valid_utterance, schema=utterance_schema)


def test_utterance_missing_required_field(utterance_schema):
    """Test that utterance missing required fields fails validation."""
    invalid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello world"
        # Missing confidence, start_time, end_time
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_utterance, schema=utterance_schema)


def test_utterance_empty_text(utterance_schema):
    """Test that utterance with empty text fails validation."""
    invalid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "",
        "confidence": 0.95,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_utterance, schema=utterance_schema)


def test_utterance_invalid_confidence_range(utterance_schema):
    """Test that utterance with confidence outside 0-1 range fails validation."""
    invalid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello world",
        "confidence": 1.5,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_utterance, schema=utterance_schema)


def test_utterance_negative_confidence(utterance_schema):
    """Test that utterance with negative confidence fails validation."""
    invalid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello world",
        "confidence": -0.1,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_utterance, schema=utterance_schema)


def test_utterance_additional_properties(utterance_schema):
    """Test that utterance with additional properties fails validation."""
    invalid_utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hello world",
        "confidence": 0.95,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "extra_field": "not allowed"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_utterance, schema=utterance_schema)