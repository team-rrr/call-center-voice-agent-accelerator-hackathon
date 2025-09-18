"""
Minimal Orchestrator Service using Azure AI Foundry agents.
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import Azure AI projects at module level
try:
    from azure.ai.projects.aio import AIProjectClient
    from azure.identity.aio import DefaultAzureCredential
    AZURE_AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Azure AI Projects not available: {e}")
    AIProjectClient = None
    DefaultAzureCredential = None
    AZURE_AI_AVAILABLE = False


class OrchestratorService:
    """Minimal service to call the Appointment-Guidelines-Orchestrator agent in Azure AI Foundry."""
    
    def __init__(self):
        self.client: Any = None
        self.orchestrator_agent_id = "asst_5Eqb4UJ43MYXj5shQFl3ubfC"
        self._azure_ai_available = False
        
    async def initialize(self):
        """Initialize the Azure AI Project Client."""
        if not AZURE_AI_AVAILABLE:
            logger.error("Azure AI Projects library not available")
            self._azure_ai_available = False
            return
            
        try:
            self._azure_ai_available = True
            
            endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
            if not endpoint:
                raise ValueError("AZURE_AI_AGENT_ENDPOINT not configured")
            
            if DefaultAzureCredential is None or AIProjectClient is None:
                raise ImportError("Azure AI Projects classes not available")
                
            credential = DefaultAzureCredential()
            self.client = AIProjectClient(endpoint=endpoint, credential=credential)
            logger.info("OrchestratorService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OrchestratorService: {e}")
            self._azure_ai_available = False
    
    async def call_orchestrator(
        self, 
        user_message: str, 
        session_id: Optional[str] = None,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call the orchestrator agent with a user message.
        
        Args:
            user_message: The caregiver's message/request
            session_id: Optional session identifier
            patient_context: Optional patient context information
            
        Returns:
            Dict containing the orchestrated response
        """
        if not self._azure_ai_available:
            return {
                "success": False,
                "error": "Azure AI Projects library not available",
                "response": "I'm sorry, but the appointment preparation system is not fully configured. Please install the required Azure AI libraries."
            }
            
        if not self.client:
            await self.initialize()
            
        if not self.client:
            return {
                "success": False,
                "error": "Failed to initialize Azure AI client",
                "response": "I'm sorry, but I'm having trouble connecting to the appointment preparation system. Please try again later."
            }
        
        try:
            # Create a thread and run the orchestrator agent in one call
            result = await self.client.agents.create_thread_and_run(
                agent_id=self.orchestrator_agent_id,
                thread={
                    "messages": [
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ]
                }
            )
            
            # Wait for completion
            completed_run = await self._wait_for_completion(result.thread_id, result.id)
            
            # Get the assistant's response from messages
            messages_paged = self.client.agents.messages.list(thread_id=result.thread_id)
            
            # Convert AsyncItemPaged to list
            messages_list = []
            async for message in messages_paged:
                messages_list.append(message)
            
            # Find the latest assistant message
            assistant_response = None
            for message in messages_list:
                if message.role == "assistant":
                    # Handle different content types
                    if hasattr(message.content[0], 'text'):
                        assistant_response = message.content[0].text.value
                    elif hasattr(message.content[0], 'value'):
                        assistant_response = message.content[0].value
                    else:
                        assistant_response = str(message.content[0])
                    break
            
            return {
                "success": True,
                "response": assistant_response or "No response received",
                "session_id": session_id,
                "thread_id": result.thread_id,
                "run_id": completed_run.id
            }
            
        except Exception as e:
            logger.error(f"Error calling orchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble connecting to the appointment preparation system. Please try again later."
            }
    
    async def _wait_for_completion(self, thread_id: str, run_id: str, max_wait_time: int = 30):
        """Wait for the agent run to complete."""
        for _ in range(max_wait_time):
            run = await self.client.agents.runs.get(thread_id=thread_id, run_id=run_id)
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
                
            await asyncio.sleep(1)
        
        raise TimeoutError("Agent run did not complete within the expected time")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.close()


# Global instance
_orchestrator_service = None

async def get_orchestrator_service() -> OrchestratorService:
    """Get the global orchestrator service instance."""
    global _orchestrator_service
    
    if _orchestrator_service is None:
        _orchestrator_service = OrchestratorService()
        await _orchestrator_service.initialize()
    
    return _orchestrator_service