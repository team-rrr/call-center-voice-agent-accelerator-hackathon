import asyncio
import logging
from typing import Any, Callable, Optional, Type, Union
import aiohttp
from functools import wraps


logger = logging.getLogger(__name__)


class RetryHelper:
    """
    Helper class for retrying transient failures with exponential backoff.
    Supports configurable retry logic for different types of errors.
    """
    
    def __init__(self, max_retries: int = 2, base_delay: float = 1.0, backoff_factor: float = 2.0, max_delay: float = 60.0):
        """
        Initialize retry helper.
        
        Args:
            max_retries: Maximum number of retry attempts (not including initial attempt)
            base_delay: Base delay in seconds for first retry
            backoff_factor: Multiplier for exponential backoff
            max_delay: Maximum delay between retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    async def retry_with_backoff(self, coro_func: Callable, *args, **kwargs) -> Any:
        """
        Retry a coroutine function with exponential backoff.
        
        Args:
            coro_func: Async function to retry
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the successful function call
            
        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                logger.debug(f"Attempt {attempt + 1} for {coro_func.__name__}")
                return await coro_func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                # Log the error
                logger.warning(f"Attempt {attempt + 1} failed for {coro_func.__name__}: {str(e)}")
                
                # Don't retry on the last attempt
                if attempt == self.max_retries:
                    logger.error(f"All {self.max_retries + 1} attempts failed for {coro_func.__name__}")
                    break
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    logger.info(f"Non-retryable error for {coro_func.__name__}: {type(e).__name__}")
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                logger.info(f"Retrying {coro_func.__name__} in {delay:.2f} seconds")
                await asyncio.sleep(delay)
        
        # Raise the last exception if all retries failed
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable based on its type and properties.
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error should be retried, False otherwise
        """
        # Network-related errors that are typically transient
        retryable_types = (
            aiohttp.ClientTimeout,
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            aiohttp.ClientPayloadError,
            ConnectionError,
            TimeoutError,
            OSError,  # Can include network-related OS errors
        )
        
        # Check if it's a known retryable type
        if isinstance(error, retryable_types):
            return True
        
        # Check HTTP status codes for aiohttp errors
        if hasattr(error, 'status'):
            status_code = getattr(error, 'status', None)
            if status_code:
                # Retry on server errors (5xx) and some client errors
                if 500 <= status_code < 600:  # Server errors
                    return True
                if status_code in [408, 429]:  # Request timeout, too many requests
                    return True
        
        # Check for specific error messages that indicate transient issues
        error_message = str(error).lower()
        transient_indicators = [
            'timeout',
            'connection reset',
            'connection refused',
            'temporarily unavailable',
            'service unavailable',
            'rate limit',
            'throttl'
        ]
        
        for indicator in transient_indicators:
            if indicator in error_message:
                return True
        
        return False


def retry_on_failure(max_retries: int = 2, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator for adding retry logic to async functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        backoff_factor: Multiplier for exponential backoff
        
    Example:
        @retry_on_failure(max_retries=3, base_delay=0.5)
        async def api_call():
            # Function that might fail transiently
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_helper = RetryHelper(max_retries, base_delay, backoff_factor)
            return await retry_helper.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator


class TranscriptionRetryHelper(RetryHelper):
    """Specialized retry helper for transcription API calls."""
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Custom logic for transcription-specific retryable errors."""
        # Use base logic first
        if super()._is_retryable_error(error):
            return True
        
        # Transcription-specific retryable conditions
        error_message = str(error).lower()
        transcription_retryable = [
            'audio format not supported',  # Sometimes transient
            'audio too short',  # Might work on retry with different segmentation
            'model temporarily unavailable'
        ]
        
        return any(indicator in error_message for indicator in transcription_retryable)


class TTSRetryHelper(RetryHelper):
    """Specialized retry helper for text-to-speech API calls."""
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Custom logic for TTS-specific retryable errors."""
        # Use base logic first
        if super()._is_retryable_error(error):
            return True
        
        # TTS-specific retryable conditions
        error_message = str(error).lower()
        tts_retryable = [
            'voice not available',  # Might become available
            'synthesis queue full',  # Temporary capacity issue
            'model loading'  # Model might finish loading
        ]
        
        return any(indicator in error_message for indicator in tts_retryable)


class LLMRetryHelper(RetryHelper):
    """Specialized retry helper for LLM API calls."""
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Custom logic for LLM-specific retryable errors."""
        # Use base logic first
        if super()._is_retryable_error(error):
            return True
        
        # LLM-specific retryable conditions
        error_message = str(error).lower()
        llm_retryable = [
            'context length exceeded',  # Might retry with truncated context
            'model overloaded',
            'capacity exceeded',
            'token limit',  # Might work with shorter input
        ]
        
        # Check for specific OpenAI error types if available
        if hasattr(error, 'error') and hasattr(error.error, 'type'):
            error_type = error.error.type
            if error_type in ['server_error', 'timeout', 'rate_limit_exceeded']:
                return True
        
        return any(indicator in error_message for indicator in llm_retryable)


# Create default instances for common use cases
transcription_retry = TranscriptionRetryHelper(max_retries=2, base_delay=1.0)
tts_retry = TTSRetryHelper(max_retries=2, base_delay=0.5)
llm_retry = LLMRetryHelper(max_retries=3, base_delay=2.0)
general_retry = RetryHelper(max_retries=2, base_delay=1.0)