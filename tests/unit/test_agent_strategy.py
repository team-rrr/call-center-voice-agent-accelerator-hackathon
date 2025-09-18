import pytest
from unittest.mock import AsyncMock
from server.models.agent import Agent, AgentStrategy, EchoAgentStrategy, AgentMessage


class MockLLMAgentStrategy(AgentStrategy):
    """Mock LLM agent strategy for testing."""
    
    def __init__(self, agent: Agent, responses: list = None):
        super().__init__(agent)
        self.responses = responses or ["I'm a mock LLM response."]
        self.call_count = 0
    
    async def process_utterance(self, utterance_text: str, context=None) -> AgentMessage:
        """Mock LLM processing."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
        return AgentMessage(
            agent=self.agent.name,
            type="response",
            payload={
                "response_text": response,
                "model_used": "mock-gpt-4",
                "tokens_used": len(utterance_text.split()) * 2,
                "context_length": len(context) if context else 0
            }
        )
    
    async def handle_interruption(self):
        """Mock interruption handling."""
        return AgentMessage(
            agent=self.agent.name,
            type="response",
            payload={
                "response_text": "I was interrupted but I understand.",
                "interruption_handled": True
            }
        )


@pytest.fixture
def test_agent():
    """Create a test agent."""
    return Agent(
        name="test_agent",
        purpose="Agent for testing",
        allowed_tools=["test_tool", "echo"],
        guardrails={"max_response_length": 500}
    )


@pytest.fixture
def echo_strategy(test_agent):
    """Create an echo agent strategy."""
    return EchoAgentStrategy(test_agent)


@pytest.fixture  
def mock_llm_strategy(test_agent):
    """Create a mock LLM agent strategy."""
    return MockLLMAgentStrategy(
        test_agent, 
        responses=["Hello there!", "How can I help?", "That's interesting."]
    )


def test_agent_model_creation(test_agent):
    """Test basic agent model functionality."""
    assert test_agent.name == "test_agent"
    assert test_agent.purpose == "Agent for testing"
    assert "test_tool" in test_agent.allowed_tools
    assert test_agent.guardrails["max_response_length"] == 500


def test_agent_tool_management(test_agent):
    """Test agent tool management methods."""
    # Test can_use_tool
    assert test_agent.can_use_tool("test_tool")
    assert test_agent.can_use_tool("echo")
    assert not test_agent.can_use_tool("nonexistent_tool")
    
    # Test add_tool
    test_agent.add_tool("new_tool")
    assert test_agent.can_use_tool("new_tool")
    
    # Test adding duplicate tool
    initial_count = len(test_agent.allowed_tools)
    test_agent.add_tool("new_tool")  # Add same tool again
    assert len(test_agent.allowed_tools) == initial_count  # Should not duplicate
    
    # Test remove_tool
    test_agent.remove_tool("test_tool")
    assert not test_agent.can_use_tool("test_tool")
    
    # Test removing nonexistent tool (should not error)
    test_agent.remove_tool("nonexistent_tool")


@pytest.mark.asyncio
async def test_echo_strategy_basic_functionality(echo_strategy):
    """Test echo agent strategy basic functionality."""
    utterance = "Hello world"
    
    message = await echo_strategy.process_utterance(utterance)
    
    assert isinstance(message, AgentMessage)
    assert message.agent == "test_agent"
    assert message.type == "response"
    assert utterance in message.payload["response_text"]
    assert message.payload["original_utterance"] == utterance


@pytest.mark.asyncio
async def test_echo_strategy_interruption_handling(echo_strategy):
    """Test echo agent strategy interruption handling."""
    message = await echo_strategy.handle_interruption()
    
    assert isinstance(message, AgentMessage)
    assert message.agent == "test_agent"
    assert message.type == "response"
    assert message.payload["interruption_handled"] is True
    assert "something else" in message.payload["response_text"]


@pytest.mark.asyncio
async def test_mock_llm_strategy_responses(mock_llm_strategy):
    """Test mock LLM strategy with different responses."""
    # Test first response
    message1 = await mock_llm_strategy.process_utterance("First question")
    assert message1.payload["response_text"] == "Hello there!"
    assert message1.payload["model_used"] == "mock-gpt-4"
    
    # Test second response (cycling through responses)
    message2 = await mock_llm_strategy.process_utterance("Second question")
    assert message2.payload["response_text"] == "How can I help?"
    
    # Test third response
    message3 = await mock_llm_strategy.process_utterance("Third question")
    assert message3.payload["response_text"] == "That's interesting."
    
    # Test cycling back to first response
    message4 = await mock_llm_strategy.process_utterance("Fourth question")
    assert message4.payload["response_text"] == "Hello there!"


@pytest.mark.asyncio
async def test_mock_llm_strategy_context_handling(mock_llm_strategy):
    """Test mock LLM strategy context handling."""
    context = {"previous_turns": ["Hello", "Hi there"], "user_id": "123"}
    
    message = await mock_llm_strategy.process_utterance("What's my ID?", context)
    
    assert message.payload["context_length"] == len(context)
    assert "tokens_used" in message.payload
    assert message.payload["tokens_used"] > 0


@pytest.mark.asyncio
async def test_agent_strategy_interface_compliance():
    """Test that custom strategies comply with the interface."""
    agent = Agent(name="test", purpose="testing")
    
    class CustomStrategy(AgentStrategy):
        async def process_utterance(self, utterance_text: str, context=None):
            return AgentMessage(
                agent=self.agent.name,
                type="response",
                payload={"custom": True}
            )
        
        async def handle_interruption(self):
            return AgentMessage(
                agent=self.agent.name,
                type="response",
                payload={"interrupted": True}
            )
    
    strategy = CustomStrategy(agent)
    
    # Test process_utterance
    message = await strategy.process_utterance("test")
    assert isinstance(message, AgentMessage)
    assert message.payload["custom"] is True
    
    # Test handle_interruption
    interrupt_message = await strategy.handle_interruption()
    assert isinstance(interrupt_message, AgentMessage)
    assert interrupt_message.payload["interrupted"] is True


def test_agent_message_model():
    """Test AgentMessage model functionality."""
    message = AgentMessage(
        agent="test_agent",
        type="error",
        payload={"error_code": "TEST_ERROR"}
    )
    
    assert message.is_error()
    assert not message.is_response()
    assert message.payload["error_code"] == "TEST_ERROR"
    
    # Test response message
    response_message = AgentMessage(
        agent="test_agent",
        type="response",
        payload={"text": "Hello"}
    )
    
    assert response_message.is_response()
    assert not response_message.is_error()


@pytest.mark.asyncio
async def test_strategy_with_different_agents():
    """Test that strategies work with different agent configurations."""
    # Agent with no tools
    simple_agent = Agent(name="simple", purpose="Simple agent")
    simple_strategy = EchoAgentStrategy(simple_agent)
    
    message = await simple_strategy.process_utterance("test")
    assert message.agent == "simple"
    
    # Agent with many tools
    complex_agent = Agent(
        name="complex",
        purpose="Complex agent",
        allowed_tools=["tool1", "tool2", "tool3"],
        guardrails={"max_tokens": 1000, "safety_level": "high"}
    )
    complex_strategy = EchoAgentStrategy(complex_agent)
    
    message = await complex_strategy.process_utterance("complex test")
    assert message.agent == "complex"
    assert "complex test" in message.payload["response_text"]


@pytest.mark.asyncio
async def test_strategy_error_handling():
    """Test strategy error handling scenarios."""
    agent = Agent(name="error_agent", purpose="Testing errors")
    
    class ErrorProneStrategy(AgentStrategy):
        async def process_utterance(self, utterance_text: str, context=None):
            if "error" in utterance_text.lower():
                return AgentMessage(
                    agent=self.agent.name,
                    type="error",
                    payload={"error": "Intentional test error"}
                )
            return AgentMessage(
                agent=self.agent.name,
                type="response", 
                payload={"text": "Normal response"}
            )
        
        async def handle_interruption(self):
            return None  # Some strategies might return None
    
    strategy = ErrorProneStrategy(agent)
    
    # Test error case
    error_message = await strategy.process_utterance("trigger error")
    assert error_message.is_error()
    assert "Intentional test error" in error_message.payload["error"]
    
    # Test normal case
    normal_message = await strategy.process_utterance("normal input")
    assert normal_message.is_response()
    
    # Test interruption that returns None
    interrupt_result = await strategy.handle_interruption()
    assert interrupt_result is None