import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path
from datetime import datetime
import uuid


@pytest.fixture
def task_schema():
    """Load the task schema from the contracts directory."""
    schema_path = Path(__file__).parent.parent.parent / "specs" / "001-what-a-voice" / "contracts" / "task.schema.json"
    with open(schema_path) as f:
        return json.load(f)


def test_valid_task_schema(task_schema):
    """Test that a valid task object passes schema validation."""
    valid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "planner",
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Should not raise ValidationError
    validate(instance=valid_task, schema=task_schema)


def test_valid_task_with_optional_fields(task_schema):
    """Test that a valid task with optional fields passes schema validation."""
    valid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "executor",
        "status": "succeeded",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result_summary": "Task completed successfully",
        "error_code": None,
        "progress": 100
    }
    
    # Should not raise ValidationError
    validate(instance=valid_task, schema=task_schema)


def test_task_missing_required_field(task_schema):
    """Test that task missing required fields fails validation."""
    invalid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "status": "queued"
        # Missing originating_agent, created_at, updated_at
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=task_schema)


def test_task_invalid_status(task_schema):
    """Test that task with invalid status fails validation."""
    invalid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "planner",
        "status": "invalid_status",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=task_schema)


def test_task_invalid_progress_range(task_schema):
    """Test that task with progress outside 0-100 range fails validation."""
    invalid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "planner",
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "progress": 150
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=task_schema)


def test_task_result_summary_too_long(task_schema):
    """Test that task with result_summary exceeding max length fails validation."""
    invalid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "planner",
        "status": "succeeded",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result_summary": "x" * 2049  # Exceeds maxLength of 2048
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=task_schema)


def test_task_error_code_too_long(task_schema):
    """Test that task with error_code exceeding max length fails validation."""
    invalid_task = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "originating_agent": "planner",
        "status": "failed",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "error_code": "x" * 129  # Exceeds maxLength of 128
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=task_schema)