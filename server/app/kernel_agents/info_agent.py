import logging
from typing import ClassVar

from .agent_base import BaseAgent  # Adjust the import path as needed

class InfoAgent(BaseAgent):
    response_text: ClassVar[str] = "InfoAgent static response: Hello from InfoAgent!"

    async def get_response(self, transcript):
        # Simple logic: echo the transcript with a prefix
        return f"InfoAgent received: {transcript}"
    def __init__(self, session_id, user_id, context):
        self.session_id = session_id
        self.user_id = user_id
        self.context = context
    async def generate_checklist(self, user_input):
        import aiofiles
        logging.info(f"InfoAgent received user input: {user_input}")
        async with aiofiles.open("app/prompts/info_agent_prompt.txt", mode="r") as f:
            prompt = await f.read()
        # ...call LLM or logic here...
        checklist = []  # TODO: Replace with actual checklist generation logic
        logging.info(f"InfoAgent generated checklist: {checklist}")
        return checklist