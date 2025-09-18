import pytest
import re


def redact_long_digits(text: str) -> str:
    """
    Redact sequences of 12 or more consecutive digits with [REDACTED].
    This is a simple regex-based implementation for the MVP.
    """
    pattern = r'\b\d{12,}\b'
    return re.sub(pattern, '[REDACTED]', text)


@pytest.mark.parametrize("input_text,expected", [
    # Test cases with 12+ digit sequences
    ("My credit card number is 1234567890123456", "My credit card number is [REDACTED]"),
    ("Call me at 123456789012", "Call me at [REDACTED]"),
    ("The ID is 999888777666555444", "The ID is [REDACTED]"),
    
    # Test cases with < 12 digits (should not be redacted)
    ("My phone is 5551234567", "My phone is 5551234567"),
    ("SSN: 123456789", "SSN: 123456789"),
    ("PIN: 1234", "PIN: 1234"),
    
    # Edge cases
    ("Exactly 12 digits: 123456789012", "Exactly 12 digits: [REDACTED]"),
    ("Thirteen digits: 1234567890123", "Thirteen digits: [REDACTED]"),
    ("Multiple long numbers: 123456789012 and 987654321098", "Multiple long numbers: [REDACTED] and [REDACTED]"),
    
    # Mixed content
    ("Order #12345 total $67.89 card 1234567890123456", "Order #12345 total $67.89 card [REDACTED]"),
    
    # No digits
    ("Hello world no numbers here", "Hello world no numbers here"),
    
    # Empty string
    ("", ""),
    
    # Digits with separators (should not match as consecutive)
    ("Credit card 1234-5678-9012-3456", "Credit card 1234-5678-9012-3456"),
    ("Phone +1 (555) 123-4567", "Phone +1 (555) 123-4567"),
    
    # Word boundaries test
    ("abc123456789012def", "abc123456789012def"),  # No word boundaries, should not match
    ("start 123456789012 end", "start [REDACTED] end"),  # With word boundaries, should match
])
def test_redact_long_digits(input_text, expected):
    """Test the redaction of long digit sequences."""
    result = redact_long_digits(input_text)
    assert result == expected


def test_redact_real_world_examples():
    """Test redaction with realistic call center scenarios."""
    # Credit card scenario
    transcript = "Yes my credit card number is 4532123456789012 and the expiration is 0525"
    result = redact_long_digits(transcript)
    assert "[REDACTED]" in result
    assert "0525" in result  # Expiration should not be redacted (< 12 digits)
    
    # Account number scenario
    transcript = "My account number is 987654321012345 please help me"
    result = redact_long_digits(transcript)
    assert result == "My account number is [REDACTED] please help me"
    
    # Multiple sensitive numbers
    transcript = "Card 1234567890123456 backup card 9876543210987654"
    result = redact_long_digits(transcript)
    assert result == "Card [REDACTED] backup card [REDACTED]"


def test_redact_preserves_other_content():
    """Test that redaction preserves all other content exactly."""
    transcript = "Hello! I need help with order #12345. My card ending in 6789 doesn't work but the full number is 1234567890123456. The amount is $99.99."
    result = redact_long_digits(transcript)
    
    # Should preserve everything except the long number
    assert "Hello!" in result
    assert "order #12345" in result
    assert "ending in 6789" in result
    assert "$99.99" in result
    assert "[REDACTED]" in result
    assert "1234567890123456" not in result


def test_redact_empty_and_none():
    """Test edge cases with empty or None inputs."""
    assert redact_long_digits("") == ""
    
    # Test with only spaces
    assert redact_long_digits("   ") == "   "
    
    # Test with only numbers less than 12 digits
    assert redact_long_digits("123") == "123"


def test_redact_performance_large_text():
    """Test redaction performance with larger text blocks."""
    # Create a large text with some long numbers
    large_text = ("This is a normal conversation. " * 100) + " Card number 1234567890123456 " + ("More normal text. " * 100)
    
    result = redact_long_digits(large_text)
    
    # Should still redact correctly
    assert "[REDACTED]" in result
    assert "1234567890123456" not in result
    assert result.count("This is a normal conversation.") == 100
    assert result.count("More normal text.") == 100


@pytest.mark.asyncio
async def test_redaction_integration():
    """Integration test for redaction in a simulated transcript context."""
    from datetime import datetime
    import uuid
    
    # Simulate a transcript with sensitive data
    utterance = {
        "id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "text": "Hi I need to update my payment method the card is 4532123456789012",
        "confidence": 0.95,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "interrupted": False
    }
    
    # Apply redaction
    utterance["text"] = redact_long_digits(utterance["text"])
    
    # Verify redaction occurred
    assert utterance["text"] == "Hi I need to update my payment method the card is [REDACTED]"
    
    # Verify other fields unchanged
    assert utterance["confidence"] == 0.95
    assert utterance["interrupted"] is False