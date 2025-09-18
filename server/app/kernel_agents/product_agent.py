import logging
from typing import Dict, List, Optional

from app.context.cosmos_memory_kernel import CosmosMemoryContext
from app.kernel_agents.agent_base import BaseAgent
from app.kernel_tools.product_tools import ProductTools
from app.models.messages_kernel import AgentType
from semantic_kernel.functions import KernelFunction


class ProductAgent(BaseAgent):
    """Product agent implementation using Semantic Kernel.

    This agent specializes in product management, development, and related tasks.
    It can provide information about products, manage inventory, handle product
    launches, analyze sales data, and coordinate with other teams like marketing
    and tech support.
    """

    def __init__(
        self,
        session_id: str,
        user_id: str,
        memory_store: CosmosMemoryContext,
        tools: Optional[List[KernelFunction]] = None,
        system_message: Optional[str] = None,
        agent_name: str = AgentType.PRODUCT.value,
        client=None,
        definition=None,
    ) -> None:
        """Initialize the Product Agent.

        Args:
            kernel: The semantic kernel instance
            session_id: The current session identifier
            user_id: The user identifier
            memory_store: The Cosmos memory context
            tools: List of tools available to this agent (optional)
            system_message: Optional system message for the agent
            agent_name: Optional name for the agent (defaults to "ProductAgent")
            config_path: Optional path to the Product tools configuration file
            client: Optional client instance
            definition: Optional definition instance
        """
        # Load configuration if tools not provided
        if not tools:
            # Get tools directly from ProductTools class
            tools_dict = ProductTools.get_all_kernel_functions()
            tools = [KernelFunction.from_method(func) for func in tools_dict.values()]

        # Use system message from config if not explicitly provided
        if not system_message:
            system_message = self.default_system_message(agent_name)

        # Use agent name from config if available
        agent_name = AgentType.PRODUCT.value

        super().__init__(
            agent_name=agent_name,
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
    ) -> "ProductAgent":
        """Asynchronously create the ProductAgent.

        Creates the Azure AI Agent for product operations.

        Returns:
            ProductAgent instance
        """

        session_id = kwargs.get("session_id")
        if not isinstance(session_id, str):
            raise TypeError("session_id must be a string")
        user_id = kwargs.get("user_id")
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a string")
        memory_store = kwargs.get("memory_store")
        if memory_store is None:
            raise TypeError("memory_store must be provided")
        tools = kwargs.get("tools", None)
        if tools is not None and not isinstance(tools, list):
            raise TypeError("tools must be a list of KernelFunction or None")
        system_message = kwargs.get("system_message", None)
        if system_message is not None and not isinstance(system_message, str):
            system_message = cls.default_system_message(kwargs.get("agent_name", AgentType.PRODUCT.value))
        agent_name = kwargs.get("agent_name")
        if not isinstance(agent_name, str) or not agent_name:
            agent_name = AgentType.PRODUCT.value
        client = kwargs.get("client")

        try:
            logging.info("Initializing ProductAgent from async init azure AI Agent")

            instructions_str = system_message if isinstance(system_message, str) else cls.default_system_message(agent_name)
            agent_definition = await cls._create_azure_ai_agent_definition(
                agent_name=agent_name,
                instructions=instructions_str,
                temperature=0.0,
                response_format=None,
            )

            return cls(
                session_id=session_id,
                user_id=user_id,
                memory_store=memory_store,
                tools=tools,
                system_message=system_message,
                agent_name=agent_name,
                client=client,
                definition=agent_definition,
            )

        except Exception as e:
            logging.error(f"Failed to create Azure AI Agent for ProductAgent: {e}")
            raise

    @staticmethod
    def default_system_message(agent_name=None) -> str:
        """Get the default system message for the agent.
        Args:
            agent_name: The name of the agent (optional)
        Returns:
            The default system message for the agent
        """
        return "You are a Product agent. You have knowledge about product management, development, and compliance guidelines. When asked to call a function, you should summarize back what was done."

    @property
    def plugins(self):
        """Get the plugins for the product agent."""
        return ProductTools.get_all_kernel_functions()

    # Explicitly inherit handle_action_request from the parent class
    # This is not technically necessary but makes the inheritance explicit
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
