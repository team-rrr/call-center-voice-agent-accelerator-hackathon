import pytest
from datetime import datetime
import uuid


class MockContextManager:
    """Mock context manager for testing context truncation."""
    
    def __init__(self, max_turns=5):
        self.max_turns = max_turns
        self.turns = []
        self.has_truncated = False
    
    def add_turn(self, turn_type, content, speaker=None):
        """Add a turn to the context."""
        turn = {
            "type": turn_type,  # "user" or "agent"
            "content": content,
            "speaker": speaker or turn_type,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        self.turns.append(turn)
        
        # Truncate if exceeding max turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
            self.has_truncated = True
    
    def get_context(self):
        """Get the current context."""
        return {
            "turns": self.turns,
            "total_turns": len(self.turns),
            "truncated": self.has_truncated
        }
    
    def clear(self):
        """Clear all context."""
        self.turns = []
        self.has_truncated = False


@pytest.fixture
def context_manager():
    """Provide a context manager with default settings."""
    return MockContextManager(max_turns=3)


def test_context_manager_basic_functionality(context_manager):
    """Test basic context manager operations."""
    # Start with empty context
    context = context_manager.get_context()
    assert context["total_turns"] == 0
    assert context["truncated"] is False
    
    # Add a user turn
    context_manager.add_turn("user", "Hello")
    context = context_manager.get_context()
    assert context["total_turns"] == 1
    assert context["turns"][0]["content"] == "Hello"
    assert context["turns"][0]["type"] == "user"


def test_context_truncation_when_exceeding_limit(context_manager):
    """Test that context is truncated when exceeding max turns."""
    # Add turns up to the limit
    context_manager.add_turn("user", "Turn 1")
    context_manager.add_turn("agent", "Response 1")
    context_manager.add_turn("user", "Turn 2")
    
    context = context_manager.get_context()
    assert context["total_turns"] == 3
    assert context["truncated"] is False
    
    # Add one more turn to trigger truncation
    context_manager.add_turn("agent", "Response 2")
    
    context = context_manager.get_context()
    assert context["total_turns"] == 3  # Still max turns
    assert context["truncated"] is True
    
    # Verify oldest turn was removed
    turn_contents = [turn["content"] for turn in context["turns"]]
    assert "Turn 1" not in turn_contents  # Oldest should be removed
    assert "Response 1" in turn_contents
    assert "Turn 2" in turn_contents
    assert "Response 2" in turn_contents


def test_context_maintains_order_after_truncation():
    """Test that context maintains chronological order after truncation."""
    context_manager = MockContextManager(max_turns=3)
    
    # Add multiple turns
    context_manager.add_turn("user", "First")
    context_manager.add_turn("agent", "Second") 
    context_manager.add_turn("user", "Third")
    context_manager.add_turn("agent", "Fourth")
    context_manager.add_turn("user", "Fifth")
    
    context = context_manager.get_context()
    turn_contents = [turn["content"] for turn in context["turns"]]
    
    # Should have last 3 turns in order
    assert turn_contents == ["Third", "Fourth", "Fifth"]


def test_context_with_different_turn_limits():
    """Test context manager with different turn limits."""
    # Test with limit of 1
    cm1 = MockContextManager(max_turns=1)
    cm1.add_turn("user", "First")
    cm1.add_turn("user", "Second")
    
    context = cm1.get_context()
    assert context["total_turns"] == 1
    assert context["turns"][0]["content"] == "Second"
    
    # Test with larger limit
    cm10 = MockContextManager(max_turns=10)
    for i in range(15):
        cm10.add_turn("user", f"Turn {i}")
    
    context = cm10.get_context()
    assert context["total_turns"] == 10
    assert context["truncated"] is True
    
    # Should have last 10 turns
    turn_contents = [turn["content"] for turn in context["turns"]]
    expected = [f"Turn {i}" for i in range(5, 15)]
    assert turn_contents == expected


def test_context_clear_functionality(context_manager):
    """Test context clearing functionality."""
    # Add some turns
    context_manager.add_turn("user", "Hello")
    context_manager.add_turn("agent", "Hi there")
    
    context = context_manager.get_context()
    assert context["total_turns"] == 2
    
    # Clear context
    context_manager.clear()
    
    context = context_manager.get_context()
    assert context["total_turns"] == 0
    assert context["truncated"] is False
    assert len(context["turns"]) == 0


def test_context_turn_metadata():
    """Test that context turns include proper metadata."""
    context_manager = MockContextManager(max_turns=5)
    context_manager.add_turn("user", "Test message", speaker="John")
    
    context = context_manager.get_context()
    turn = context["turns"][0]
    
    # Verify all expected fields are present
    assert "type" in turn
    assert "content" in turn
    assert "speaker" in turn
    assert "timestamp" in turn
    assert "id" in turn
    
    # Verify values
    assert turn["type"] == "user"
    assert turn["content"] == "Test message"
    assert turn["speaker"] == "John"
    
    # Verify timestamp format (basic check)
    assert "T" in turn["timestamp"]
    
    # Verify ID is valid UUID
    uuid.UUID(turn["id"])


@pytest.mark.asyncio
async def test_context_integration_with_session():
    """Integration test for context management within a session."""
    session_id = str(uuid.uuid4())
    context_manager = MockContextManager(max_turns=4)
    
    # Simulate a conversation
    conversation = [
        ("user", "I need help with my order"),
        ("agent", "I'd be happy to help! What's your order number?"),
        ("user", "It's order 12345"),
        ("agent", "Let me look that up for you"),
        ("user", "Actually, I also have a question about returns"),
        ("agent", "Sure, I can help with that too")
    ]
    
    for turn_type, content in conversation:
        context_manager.add_turn(turn_type, content)
    
    final_context = context_manager.get_context()
    
    # Should have been truncated to last 4 turns
    assert final_context["total_turns"] == 4
    assert final_context["truncated"] is True
    
    # Verify we have the most recent conversation
    recent_contents = [turn["content"] for turn in final_context["turns"]]
    expected_recent = [
        "It's order 12345",
        "Let me look that up for you", 
        "Actually, I also have a question about returns",
        "Sure, I can help with that too"
    ]
    assert recent_contents == expected_recent