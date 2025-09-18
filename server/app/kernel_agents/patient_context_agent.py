import logging
from .agent_base import BaseAgent

class PatientContextAgent(BaseAgent):
	async def get_patient_context(self, user_input):
		logging.info(f"PatientContextAgent received user input: {user_input}")
		# TODO: Replace with actual patient context retrieval logic
		patient_data = {}  # Dummy data
		logging.info(f"PatientContextAgent retrieved patient data: {patient_data}")
		return patient_data
