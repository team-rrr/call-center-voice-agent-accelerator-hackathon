import pytest
import asyncio
from unittest.mock import AsyncMock
import aiohttp


class RetryHelper:
    """Helper class for retrying transient failures with exponential backoff."""
    
    def __init__(self, max_retries: int = 2, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
    
    async def retry_with_backoff(self, coro_func, *args, **kwargs):
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
                return await coro_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Don't retry on the last attempt
                if attempt == self.max_retries:
                    break
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    break
                
                # Calculate delay with exponential backoff
                delay = self.base_delay * (self.backoff_factor ** attempt)
                await asyncio.sleep(delay)
        
        # Raise the last exception if all retries failed
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        # Network-related errors that are typically retryable
        retryable_types = (
            aiohttp.ServerTimeoutError,
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            ConnectionError,
            TimeoutError,
        )
        
        # HTTP status codes that are retryable (5xx server errors)
        if hasattr(error, 'status') and hasattr(error.status, '__int__'):
            if 500 <= int(error.status) < 600:
                return True
        
        return isinstance(error, retryable_types)


# Test the retry helper
@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Test that retry helper returns immediately on successful first attempt."""
    retry_helper = RetryHelper(max_retries=2)
    
    async def successful_function():
        return "success"
    
    result = await retry_helper.retry_with_backoff(successful_function)
    assert result == "success"


@pytest.mark.asyncio
async def test_retry_success_after_failures():
    """Test that retry helper succeeds after some failures."""
    retry_helper = RetryHelper(max_retries=2, base_delay=0.01)  # Fast for testing
    
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:  # Fail first 2 attempts
            raise aiohttp.ServerTimeoutError("Timeout")
        return "success"
    
    result = await retry_helper.retry_with_backoff(flaky_function)
    assert result == "success"
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_retry_exhaustion():
    """Test that retry helper raises exception after exhausting retries."""
    retry_helper = RetryHelper(max_retries=2, base_delay=0.01)
    
    async def always_failing_function():
        raise aiohttp.ServerTimeoutError("Always fails")
    
    with pytest.raises(aiohttp.ServerTimeoutError, match="Always fails"):
        await retry_helper.retry_with_backoff(always_failing_function)


@pytest.mark.asyncio
async def test_non_retryable_error():
    """Test that non-retryable errors are not retried."""
    retry_helper = RetryHelper(max_retries=2)
    
    attempt_count = 0
    
    async def non_retryable_error_function():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("This should not be retried")
    
    with pytest.raises(ValueError, match="This should not be retried"):
        await retry_helper.retry_with_backoff(non_retryable_error_function)
    
    # Should only attempt once for non-retryable errors
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_retry_with_arguments():
    """Test that retry helper passes arguments correctly."""
    retry_helper = RetryHelper(max_retries=1, base_delay=0.01)
    
    async def function_with_args(arg1, arg2, kwarg1=None):
        return f"{arg1}-{arg2}-{kwarg1}"
    
    result = await retry_helper.retry_with_backoff(
        function_with_args, "a", "b", kwarg1="c"
    )
    assert result == "a-b-c"


@pytest.mark.asyncio
async def test_retry_delay_calculation():
    """Test that retry delays follow exponential backoff."""
    retry_helper = RetryHelper(max_retries=2, base_delay=0.1, backoff_factor=2.0)
    
    delays = []
    original_sleep = asyncio.sleep
    
    async def mock_sleep(delay):
        delays.append(delay)
        # Don't actually sleep to keep test fast
        pass
    
    # Patch asyncio.sleep temporarily
    asyncio.sleep = mock_sleep
    
    try:
        async def always_failing():
            raise aiohttp.ServerTimeoutError("Fail")
        
        with pytest.raises(aiohttp.ServerTimeoutError):
            await retry_helper.retry_with_backoff(always_failing)
        
        # Should have delays: 0.1, 0.2 (base_delay * backoff_factor^attempt)
        assert len(delays) == 2
        assert delays[0] == 0.1
        assert delays[1] == 0.2
        
    finally:
        # Restore original sleep
        asyncio.sleep = original_sleep


def test_retryable_error_detection():
    """Test detection of retryable vs non-retryable errors."""
    retry_helper = RetryHelper()
    
    # Retryable errors
    assert retry_helper._is_retryable_error(aiohttp.ServerTimeoutError())
    assert retry_helper._is_retryable_error(aiohttp.ClientConnectionError())
    assert retry_helper._is_retryable_error(ConnectionError())
    assert retry_helper._is_retryable_error(TimeoutError())
    
    # Non-retryable errors
    assert not retry_helper._is_retryable_error(ValueError())
    assert not retry_helper._is_retryable_error(KeyError())
    assert not retry_helper._is_retryable_error(TypeError())


@pytest.mark.asyncio
async def test_retry_with_mock():
    """Test retry helper with mock functions."""
    retry_helper = RetryHelper(max_retries=1, base_delay=0.01)
    
    mock_func = AsyncMock()
    mock_func.side_effect = [aiohttp.ServerTimeoutError("First fail"), "success"]
    
    result = await retry_helper.retry_with_backoff(mock_func, "arg1", kwarg="value")
    
    assert result == "success"
    assert mock_func.call_count == 2
    mock_func.assert_called_with("arg1", kwarg="value")
