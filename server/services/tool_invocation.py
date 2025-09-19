from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

from models.task import ToolInvocation


logger = logging.getLogger(__name__)


class ToolInvocationService:
    """
    Service for logging and managing tool invocations.
    In MVP, this only logs placeholder tool calls without external side effects.
    """
    
    def __init__(self):
        """Initialize tool invocation service."""
        self._invocations: Dict[str, ToolInvocation] = {}
        self._allowed_tools = {
            "echo": "Simple echo tool for testing",
            "placeholder_action": "Placeholder action tool",
            "status_check": "Check status tool",
            "information_lookup": "Information lookup tool"
        }
    
    async def log_tool_invocation(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        task_id: Optional[str] = None
    ) -> ToolInvocation:
        """
        Log a tool invocation request.
        
        Args:
            tool_name: Name of the tool being invoked
            parameters: Parameters for the tool call
            task_id: Optional associated task ID
            
        Returns:
            ToolInvocation object
        """
        # Sanitize parameters to remove sensitive data
        sanitized_params = self._sanitize_parameters(parameters.copy())
        
        invocation = ToolInvocation(
            task_id=task_id,
            tool_name=tool_name,
            parameters=sanitized_params,
            outcome_status="pending"
        )
        
        self._invocations[invocation.id] = invocation
        
        logger.info(f"Logged tool invocation: {tool_name} (ID: {invocation.id})")
        logger.debug(f"Tool parameters: {sanitized_params}")
        
        return invocation
    
    async def execute_placeholder_tool(self, invocation: ToolInvocation) -> ToolInvocation:
        """
        Execute a placeholder tool (no external side effects in MVP).
        
        Args:
            invocation: Tool invocation to execute
            
        Returns:
            Updated invocation with results
        """
        start_time = datetime.now()
        
        try:
            # Simulate tool execution time
            import asyncio
            await asyncio.sleep(0.1)  # Brief simulation delay
            
            # Check if tool is allowed
            if invocation.tool_name not in self._allowed_tools:
                raise ValueError(f"Tool '{invocation.tool_name}' is not allowed")
            
            # Simulate tool execution based on tool type
            if invocation.tool_name == "echo":
                result = f"Echo: {invocation.parameters.get('message', 'No message')}"
            elif invocation.tool_name == "placeholder_action":
                result = f"Placeholder action executed with parameters: {invocation.parameters}"
            elif invocation.tool_name == "status_check":
                result = "Status: All systems operational"
            elif invocation.tool_name == "information_lookup":
                query = invocation.parameters.get('query', 'unknown')
                result = f"Information lookup for '{query}': Mock result"
            else:
                result = f"Tool '{invocation.tool_name}' executed successfully"
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            invocation.mark_success(duration)
            
            logger.info(f"Tool invocation {invocation.id} completed successfully")
            logger.debug(f"Tool result: {result}")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            invocation.mark_error(duration)
            
            logger.error(f"Tool invocation {invocation.id} failed: {str(e)}")
        
        return invocation
    
    async def invoke_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        task_id: Optional[str] = None
    ) -> ToolInvocation:
        """
        Log and execute a tool invocation.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
            task_id: Optional associated task ID
            
        Returns:
            Completed tool invocation
        """
        # Log the invocation
        invocation = await self.log_tool_invocation(tool_name, parameters, task_id)
        
        # Execute the tool (placeholder in MVP)
        completed_invocation = await self.execute_placeholder_tool(invocation)
        
        return completed_invocation
    
    def get_invocation(self, invocation_id: str) -> Optional[ToolInvocation]:
        """
        Get a tool invocation by ID.
        
        Args:
            invocation_id: Invocation identifier
            
        Returns:
            ToolInvocation object or None if not found
        """
        return self._invocations.get(invocation_id)
    
    def list_invocations(self, task_id: Optional[str] = None, limit: int = 100) -> List[ToolInvocation]:
        """
        List tool invocations, optionally filtered by task.
        
        Args:
            task_id: Optional task ID to filter by
            limit: Maximum number of invocations to return
            
        Returns:
            List of tool invocations
        """
        invocations = list(self._invocations.values())
        
        if task_id:
            invocations = [inv for inv in invocations if inv.task_id == task_id]
        
        # Sort by timestamp (most recent first)
        invocations.sort(key=lambda x: x.timestamp, reverse=True)
        
        return invocations[:limit]
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """
        Get tool invocation statistics.
        
        Returns:
            Dictionary with tool usage statistics
        """
        total_invocations = len(self._invocations)
        
        if total_invocations == 0:
            return {
                "total_invocations": 0,
                "success_rate": 0.0,
                "tool_usage": {},
                "avg_duration": 0.0
            }
        
        successful = sum(1 for inv in self._invocations.values() if inv.outcome_status == "success")
        success_rate = successful / total_invocations
        
        # Tool usage counts
        tool_usage = {}
        total_duration = 0
        duration_count = 0
        
        for inv in self._invocations.values():
            tool_usage[inv.tool_name] = tool_usage.get(inv.tool_name, 0) + 1
            
            if inv.duration is not None:
                total_duration += inv.duration
                duration_count += 1
        
        avg_duration = total_duration / duration_count if duration_count > 0 else 0.0
        
        return {
            "total_invocations": total_invocations,
            "success_rate": success_rate,
            "tool_usage": tool_usage,
            "avg_duration": avg_duration,
            "allowed_tools": list(self._allowed_tools.keys())
        }
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize parameters to remove sensitive data.
        
        Args:
            parameters: Raw parameters
            
        Returns:
            Sanitized parameters safe for logging
        """
        # Remove or mask sensitive parameter names
        sensitive_keys = ["password", "token", "key", "secret", "credential", "auth"]
        
        for key in list(parameters.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                parameters[key] = "[REDACTED]"
            
            # Limit string values to reasonable length for logging
            if isinstance(parameters[key], str) and len(parameters[key]) > 500:
                parameters[key] = parameters[key][:500] + "...[TRUNCATED]"
        
        return parameters