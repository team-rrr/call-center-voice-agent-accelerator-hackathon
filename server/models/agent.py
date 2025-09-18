from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import uuid


class Agent(BaseModel):
    """Agent model representing an intelligent agent in the system."""
    
    name: str = Field(..., description="Agent name/identifier")
    version: str = Field(default="1.0.0", description="Agent version")
    purpose: str = Field(..., description="Descriptive purpose of the agent")
    allowed_tools: List[str] = Field(default_factory=list, description="List of tools this agent can use")
    guardrails: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration object for guardrails")
    
    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent is allowed to use a specific tool."""
        return tool_name in self.allowed_tools
    
    def add_tool(self, tool_name: str) -> None:
        """Add a tool to the agent's allowed tools."""
        if tool_name not in self.allowed_tools:
            self.allowed_tools.append(tool_name)
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's allowed tools."""
        if tool_name in self.allowed_tools:
            self.allowed_tools.remove(tool_name)


class AgentMessage(BaseModel):
    """Agent message model for communication between agents."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique message identifier")
    agent: str = Field(..., description="Name of the agent sending the message")
    type: str = Field(..., description="Message type: plan, action, observation, response, or error")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Optional message payload")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_error(self) -> bool:
        """Check if this is an error message."""
        return self.type == "error"
    
    def is_response(self) -> bool:
        """Check if this is a response message."""
        return self.type == "response"


class AgentStrategy(ABC):
    """Abstract base class for agent strategies."""
    
    def __init__(self, agent: Agent):
        self.agent = agent
    
    @abstractmethod
    async def process_utterance(self, utterance_text: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Process an utterance and return an agent message."""
        pass
    
    @abstractmethod
    async def handle_interruption(self) -> Optional[AgentMessage]:
        """Handle interruption scenario."""
        pass


class EchoAgentStrategy(AgentStrategy):
    """Simple echo agent strategy for testing."""
    
    async def process_utterance(self, utterance_text: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Echo back the utterance with a simple response."""
        response_text = f"I heard you say: {utterance_text}"
        
        return AgentMessage(
            agent=self.agent.name,
            type="response",
            payload={
                "response_text": response_text,
                "original_utterance": utterance_text
            }
        )
    
    async def handle_interruption(self) -> Optional[AgentMessage]:
        """Handle interruption by acknowledging it."""
        return AgentMessage(
            agent=self.agent.name,
            type="response", 
            payload={
                "response_text": "I understand you want to say something else.",
                "interruption_handled": True
            }
        )