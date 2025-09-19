from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

from models.agent import Agent, AgentStrategy, EchoAgentStrategy, AgentMessage
from models.utterance import Utterance
from services.context_manager import ContextManager


logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    Agent runtime for managing agent strategies and processing utterances.
    Supports pluggable agent strategies and context management.
    """
    
    def __init__(self):
        """Initialize agent runtime."""
        self._strategies: Dict[str, AgentStrategy] = {}
        self._default_strategy: Optional[str] = None
        self._context_managers: Dict[str, ContextManager] = {}
        
        # Initialize default echo agent
        self._setup_default_agents()
    
    def _setup_default_agents(self) -> None:
        """Setup default agent strategies."""
        # Create default echo agent
        echo_agent = Agent(
            name="echo",
            purpose="Echo agent for testing and fallback",
            allowed_tools=["echo"],
            version="1.0.0"
        )
        
        echo_strategy = EchoAgentStrategy(echo_agent)
        self.register_strategy("echo", echo_strategy)
        self.set_default_strategy("echo")
    
    def register_strategy(self, name: str, strategy: AgentStrategy) -> None:
        """
        Register an agent strategy.
        
        Args:
            name: Strategy name
            strategy: Agent strategy instance
        """
        self._strategies[name] = strategy
        logger.info(f"Registered agent strategy: {name}")
    
    def set_default_strategy(self, name: str) -> None:
        """
        Set the default agent strategy.
        
        Args:
            name: Name of strategy to use as default
        """
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not registered")
        
        self._default_strategy = name
        logger.info(f"Set default agent strategy: {name}")
    
    def get_strategy(self, name: Optional[str] = None) -> Optional[AgentStrategy]:
        """
        Get an agent strategy by name.
        
        Args:
            name: Strategy name, or None for default
            
        Returns:
            Agent strategy instance, or None if not found
        """
        strategy_name = name or self._default_strategy
        return self._strategies.get(strategy_name)
    
    def get_context_manager(self, session_id: str) -> ContextManager:
        """
        Get or create context manager for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context manager instance
        """
        if session_id not in self._context_managers:
            self._context_managers[session_id] = ContextManager(max_turns=10)
        
        return self._context_managers[session_id]
    
    async def process_utterance(self, utterance: Utterance, strategy_name: Optional[str] = None) -> Optional[AgentMessage]:
        """
        Process an utterance using the specified or default agent strategy.
        
        Args:
            utterance: User utterance to process
            strategy_name: Optional strategy name, uses default if None
            
        Returns:
            Agent response message, or None if processing failed
        """
        try:
            strategy = self.get_strategy(strategy_name)
            if not strategy:
                logger.error(f"No agent strategy available: {strategy_name}")
                return None
            
            # Get context for this session
            context_manager = self.get_context_manager(utterance.session_id)
            
            # Add user utterance to context
            context_manager.add_user_utterance(
                utterance.text, 
                utterance.confidence, 
                utterance.interrupted
            )
            
            # Get context for agent processing
            context = context_manager.get_context()
            
            # Process utterance with agent
            response = await strategy.process_utterance(utterance.text, context)
            
            # Add agent response to context
            if response and response.payload and "response_text" in response.payload:
                context_manager.add_agent_response(
                    response.payload["response_text"],
                    response.agent
                )
            
            logger.debug(f"Processed utterance for session {utterance.session_id} with agent {response.agent if response else 'none'}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process utterance: {str(e)}")
            return None
    
    async def handle_interruption(self, session_id: str, strategy_name: Optional[str] = None) -> Optional[AgentMessage]:
        """
        Handle user interruption (barge-in).
        
        Args:
            session_id: Session where interruption occurred
            strategy_name: Optional strategy name
            
        Returns:
            Agent response to interruption, or None
        """
        try:
            strategy = self.get_strategy(strategy_name)
            if not strategy:
                logger.error(f"No agent strategy available for interruption: {strategy_name}")
                return None
            
            response = await strategy.handle_interruption()
            
            # Add interruption handling to context
            if response and response.payload and "response_text" in response.payload:
                context_manager = self.get_context_manager(session_id)
                context_manager.add_agent_response(
                    response.payload["response_text"],
                    response.agent
                )
            
            logger.debug(f"Handled interruption for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to handle interruption: {str(e)}")
            return None
    
    def clear_session_context(self, session_id: str) -> None:
        """
        Clear context for a session.
        
        Args:
            session_id: Session to clear context for
        """
        if session_id in self._context_managers:
            self._context_managers[session_id].clear_context()
            logger.debug(f"Cleared context for session {session_id}")
    
    def remove_session_context(self, session_id: str) -> None:
        """
        Remove context manager for a session (session ended).
        
        Args:
            session_id: Session to remove context for
        """
        if session_id in self._context_managers:
            del self._context_managers[session_id]
            logger.debug(f"Removed context manager for session {session_id}")
    
    def get_runtime_status(self) -> Dict[str, Any]:
        """
        Get agent runtime status.
        
        Returns:
            Runtime status information
        """
        return {
            "registered_strategies": list(self._strategies.keys()),
            "default_strategy": self._default_strategy,
            "active_sessions": len(self._context_managers),
            "last_check": datetime.now().isoformat()
        }
    
    def get_session_context_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context summary for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context summary or None if session not found
        """
        if session_id in self._context_managers:
            context_manager = self._context_managers[session_id]
            return context_manager.get_conversation_summary()
        
        return None