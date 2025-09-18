import logging
from app.kernel_agents.agent_factory import AgentFactory
from app.orchestrator.group_chat_manager import GroupChatManager
from app.kernel_agents.agent_factory import AgentType
from app.kernel_agents.agent_base import BaseAgent 


class Orchestrator:
    def __init__(self, session_id, user_id, context):
        self.agent_factory = AgentFactory()
        self.group_chat_manager = GroupChatManager(self.session_id, self.user_id, self.context.get("memory_store"))
        self.session_id = session_id
        self.user_id = user_id
        self.context = context

    async def handle_voice_call(self, user_input):
        logging.info(f"Voice call started with input: {user_input}")
        # Step 1: InfoAgent provides checklist
        info_agent = await self.agent_factory.create_agent(AgentType.INFO_AGENT, self.session_id, self.user_id, self.context)
        checklist = await info_agent.generate_checklist(user_input)

        # Step 2: PatientContextAgent retrieves patient data
        context_agent = await self.agent_factory.create_agent(AgentType.PATIENT_CONTEXT_AGENT, self.session_id, self.user_id, self.context)
        patient_data = await context_agent.get_patient_context(user_input)

        # Step 3: ActionAgent builds and sends checklist
        action_agent = await self.agent_factory.create_agent(AgentType.ACTION_AGENT, self.session_id, self.user_id, self.context)
        final_checklist = await action_agent.build_checklist(checklist, patient_data)
        logging.info(f"Final checklist: {final_checklist}")
        return final_checklist