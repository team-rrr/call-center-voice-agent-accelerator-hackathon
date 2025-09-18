import logging
from typing import Dict, List, Optional

from app.context.cosmos_memory_kernel import CosmosMemoryContext
from app.kernel_agents.agent_base import BaseAgent
from app.kernel_tools.generic_tools import GenericTools
from app.models.messages_kernel import AgentType
from semantic_kernel.functions import KernelFunction


class GenericAgent(BaseAgent):
    """Generic agent implementation using Semantic Kernel."""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        memory_store: CosmosMemoryContext,
        tools: Optional[List[KernelFunction]] = None,
        system_message: Optional[str] = None,
        agent_name: str = AgentType.GENERIC.value,
        client=None,
        definition=None,
    ) -> None:
        """Initialize the Generic Agent.

        Args:
            session_id: The current session identifier
            user_id: The user identifier
            memory_store: The Cosmos memory context
            tools: List of tools available to this agent (optional)
            system_message: Optional system message for the agent
            agent_name: Optional name for the agent (defaults to "GenericAgent")
            config_path: Optional path to the Generic tools configuration file
            client: Optional client instance
            definition: Optional definition instance
        """
        # Load configuration if tools not provided
        if not tools:
            # Get tools directly from GenericTools class
            tools_dict = GenericTools.get_all_kernel_functions()

            tools = [KernelFunction.from_method(func) for func in tools_dict.values()]

            # Use system message from config if not explicitly provided
            if not system_message:
                system_message = self.default_system_message(agent_name)

            # Use agent name from config if available
            agent_name = AgentType.GENERIC.value

        # Call the parent initializer
        super().__init__(
            agent_name=agent_name if agent_name is not None else AgentType.GENERIC.value,
            session_id=session_id,
            user_id=user_id,
            memory_store=memory_store,
            tools=tools,
            system_message=system_message,
            client=client,
            definition=definition,
        )

    @classmethod
    async def create(
        cls,
        **kwargs,
    ) -> "GenericAgent":
        """Asynchronously create the PlannerAgent.

        Creates the Azure AI Agent for planning operations.

        Returns:
            GenericAgent instance
        """

        session_id = kwargs.get("session_id")
        user_id = kwargs.get("user_id")
        memory_store = kwargs.get("memory_store")
        tools = kwargs.get("tools", None)
        system_message = kwargs.get("system_message", None)
        agent_name = kwargs.get("agent_name")
        client = kwargs.get("client")

        # Ensure required arguments are not None
        if session_id is None:
            raise ValueError("session_id is required and cannot be None")
        if user_id is None:
            raise ValueError("user_id is required and cannot be None")
        if memory_store is None:
            raise ValueError("memory_store is required and cannot be None")

        try:
            logging.info("Initializing GenericAgent from async init azure AI Agent")

            # Create the Azure AI Agent using AppConfig with string instructions
            agent_definition = await cls._create_azure_ai_agent_definition(
                agent_name=agent_name if agent_name is not None else AgentType.GENERIC.value,
                instructions=system_message if system_message is not None else cls.default_system_message(agent_name),  # Ensure instructions is always a string
                temperature=0.0,
                response_format=None,
            )

            return cls(
                session_id=session_id,
                user_id=user_id,
                memory_store=memory_store,
                tools=tools,
                system_message=system_message,
                agent_name=agent_name if agent_name is not None else AgentType.GENERIC.value,
                client=client,
                definition=agent_definition,
            )

        except Exception as e:
            logging.error(f"Failed to create Azure AI Agent for PlannerAgent: {e}")
            raise

    @staticmethod
    def default_system_message(agent_name=None) -> str:
        """Get the default system message for the agent.
        Args:
            agent_name: The name of the agent (optional)
        Returns:
            The default system message for the agent
        """
        return "You are a Generic agent that can help with general questions and provide basic information. You can search for information and perform simple calculations."

    @property
    def plugins(self):
        """Get the plugins for the generic agent."""
        return GenericTools.get_all_kernel_functions()

    # Explicitly inherit handle_action_request from the parent class
    async def handle_action_request(self, action_request_json: str) -> str:
        """Handle an action request from another agent or the system.

        This method is inherited from BaseAgent but explicitly included here for clarity.

        Args:
            action_request_json: The action request as a JSON string

        Returns:
            A JSON string containing the action response
        """
        from app.models.messages_kernel import ActionRequest
        import json

        action_request_dict = json.loads(action_request_json)
        action_request = ActionRequest(**action_request_dict)
        return await super().handle_action_request(action_request)
