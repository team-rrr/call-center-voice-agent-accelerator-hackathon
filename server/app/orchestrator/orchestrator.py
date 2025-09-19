import logging
from app.orchestrator.simple_agents import (
    simulate_sample_conversation,
    AgentTurn,
    SimpleInfoAgent,
    SimplePatientContextAgent,
    SimpleActionAgent,
)


class Orchestrator:
    def __init__(self, session_id: str, user_id: str, context: dict | None = None):
        self.session_id = session_id
        self.user_id = user_id
        self.context = context or {}

    def simulate_voice_call(self, user_input: str) -> list[dict]:
        logging.info("Simulating voice call for session=%s user=%s", self.session_id, self.user_id)
        turns: list[AgentTurn] = simulate_sample_conversation(user_input)
        serialized = [
            {
                "role": t.role,
                "prompt": t.prompt,
                "response": t.response,
            }
            for t in turns
        ]
        logging.info("Simulation produced %d turns", len(serialized))
        return serialized

    # --- Simple classification & routing ---
    def classify(self, user_input: str) -> str:
        text = user_input.lower()
        if any(k in text for k in ["what should i bring", "prepare", "checklist", "appointment"]):
            return "InfoAgent"
        if any(k in text for k in ["diagnosis", "ekg", "test", "condition", "medical history"]):
            return "PatientContextAgent"
        if any(k in text for k in ["send", "email", "phone", "final", "list ready"]):
            return "ActionAgent"
        # default to info agent as a safe helper
        return "InfoAgent"

    def route_user_input(self, user_input: str) -> dict:
        agent = self.classify(user_input)
        if agent == "InfoAgent":
            return {"role": agent, "prompt": SimpleInfoAgent.prompt, "response": SimpleInfoAgent.response}
        if agent == "PatientContextAgent":
            return {"role": agent, "prompt": SimplePatientContextAgent.prompt, "response": SimplePatientContextAgent.response}
        if agent == "ActionAgent":
            return {"role": agent, "prompt": SimpleActionAgent.prompt, "response": SimpleActionAgent.response}
        return {"role": "Unknown", "prompt": "", "response": "I'm not sure how to help with that yet."}

    def build_agent_instructions(self, agent: str, user_input: str, history: list[dict]) -> str:
        recent = history[-3:]
        history_snippet = "\n".join(
            f"{h['role']}: {h['content']}" for h in recent if 'role' in h and 'content' in h
        ) or "(no prior context)"
        base_map = {
            "InfoAgent": SimpleInfoAgent.prompt,
            "PatientContextAgent": SimplePatientContextAgent.prompt,
            "ActionAgent": SimpleActionAgent.prompt,
        }
        base = base_map.get(agent, "You are a helpful assistant.")
        return (
            f"{base}\n--- Conversation Context ---\n{history_snippet}\n--- User Input ---\n{user_input}\n"
            "Respond appropriately. If requesting sending or delivery, ask for preferred channel."
        )

    # Backwards compatibility wrapper name (was async before)
    async def handle_voice_call(self, user_input: str):
        return self.simulate_voice_call(user_input)