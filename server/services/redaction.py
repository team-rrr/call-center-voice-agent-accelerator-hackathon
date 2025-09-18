import re
from typing import Optional


def redact_long_digits(text: str, replacement: str = "[REDACTED]", min_digits: int = 12) -> str:
    """
    Redact sequences of consecutive digits that meet or exceed the minimum length.
    
    This is a simple regex-based implementation for the MVP to reduce accidental 
    leakage of obvious sensitive numbers like credit cards, account numbers, etc.
    
    Args:
        text: Input text to process
        replacement: String to replace matches with
        min_digits: Minimum number of consecutive digits to redact (default 12)
    
    Returns:
        Text with long digit sequences redacted
    
    Examples:
        >>> redact_long_digits("Card number 1234567890123456")
        "Card number [REDACTED]"
        
        >>> redact_long_digits("Phone 5551234567")  # < 12 digits, not redacted
        "Phone 5551234567"
    """
    if not text:
        return text
    
    # Pattern to match sequences of min_digits or more consecutive digits
    # \b ensures word boundaries to avoid partial matches
    pattern = rf'\b\d{{{min_digits},}}\b'
    
    return re.sub(pattern, replacement, text)


def redact_patterns(text: str, patterns: Optional[list] = None) -> str:
    """
    Redact text based on multiple patterns.
    
    Args:
        text: Input text to process
        patterns: List of (pattern, replacement) tuples. If None, uses default patterns.
    
    Returns:
        Text with patterns redacted
    """
    if not text:
        return text
    
    if patterns is None:
        # Default patterns for common sensitive data
        patterns = [
            # 12+ consecutive digits (credit cards, account numbers, etc.)
            (r'\b\d{12,}\b', '[REDACTED]'),
            # SSN-like patterns (XXX-XX-XXXX)
            (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED-SSN]'),
            # Phone numbers with parentheses and dashes
            (r'\(\d{3}\)\s*\d{3}-\d{4}', '[REDACTED-PHONE]'),
        ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    
    return result


def sanitize_for_logging(text: str, max_length: int = 200) -> str:
    """
    Sanitize text for safe logging by redacting sensitive data and truncating.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum length of output text
    
    Returns:
        Sanitized text safe for logging
    """
    if not text:
        return text
    
    # First redact sensitive patterns
    sanitized = redact_long_digits(text)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length - 3] + "..."
    
    return sanitized


def mask_audio_references(text: str) -> str:
    """
    Mask references to audio data or binary content in logs.
    
    Args:
        text: Input text that might contain audio references
    
    Returns:
        Text with audio references masked
    """
    if not text:
        return text
    
    # Patterns that might indicate audio or binary data
    patterns = [
        (r'data:audio/[^;]+;base64,[A-Za-z0-9+/=]+', '[AUDIO-DATA-MASKED]'),
        (r'audio_data=[A-Za-z0-9+/=]{20,}', 'audio_data=[MASKED]'),
        (r'payload=[A-Za-z0-9+/=]{50,}', 'payload=[MASKED]'),
        (r'base64:[A-Za-z0-9+/=]{50,}', 'base64:[MASKED]')
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    
    return result


def redact_api_secrets(text: str) -> str:
    """
    Redact API keys, tokens, and other secrets from text.
    
    Args:
        text: Input text that might contain secrets
    
    Returns:
        Text with secrets redacted
    """
    if not text:
        return text
    
    # Common patterns for API keys and tokens
    patterns = [
        # Generic API key patterns
        (r'api[_-]?key["\s]*[:=]["\s]*[A-Za-z0-9+/]{20,}', 'api_key="[REDACTED]"'),
        (r'token["\s]*[:=]["\s]*[A-Za-z0-9+/]{20,}', 'token="[REDACTED]"'),
        (r'secret["\s]*[:=]["\s]*[A-Za-z0-9+/]{20,}', 'secret="[REDACTED]"'),
        
        # Bearer tokens
        (r'Bearer\s+[A-Za-z0-9+/]{20,}', 'Bearer [REDACTED]'),
        
        # Azure connection strings
        (r'endpoint=https://[^;]+;accesskey=[^;]+', 'endpoint=[REDACTED];accesskey=[REDACTED]'),
        
        # OpenAI API keys (start with sk-)
        (r'sk-[A-Za-z0-9]{48}', '[REDACTED-OPENAI-KEY]'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def comprehensive_redaction(text: str) -> str:
    """
    Apply comprehensive redaction including digits, secrets, and audio data.
    
    Args:
        text: Input text to redact
    
    Returns:
        Fully redacted text safe for logging and storage
    """
    if not text:
        return text
    
    # Apply all redaction methods
    result = redact_long_digits(text)
    result = redact_api_secrets(result)
    result = mask_audio_references(result)
    
    return result