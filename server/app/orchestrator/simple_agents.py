import logging
from dataclasses import dataclass

@dataclass
class AgentTurn:
    role: str
    prompt: str
    response: str

class SimpleInfoAgent:
    prompt = ("You are a helpful assistant that provides caregivers with guidance on preparing for medical appointments. "
              "When asked about what to bring to a cardiology visit, respond with a clear, friendly checklist that includes medical history, medication list, symptom log, family history, and questions for the doctor. "
              "Include links to helpful resources when appropriate. Keep responses concise and easy to follow.")
    response = ("To prepare for your mother’s cardiology appointment, bring her recent medical records, a list of current medications, a log of symptoms, and any questions you’d like to ask. "
                "You can use this printable medication form: https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf and this question builder: https://www.ahrq.gov/questions/question-builder/online.html.")

class SimplePatientContextAgent:
    prompt = ("You are a clinical assistant that retrieves relevant patient context for upcoming appointments. When prompted, you provide recent diagnoses, conditions, and test results from the patient’s record. "
              "If no data is available, respond with a polite message and suggest what the caregiver might bring manually. Do not speculate or offer medical advice.")
    response = ("Your mother’s recent diagnoses include hypertension and atrial fibrillation. Her last EKG was performed two months ago and showed mild arrhythmia. I’ve included these in the checklist.")

class SimpleActionAgent:
    prompt = ("You are a task-oriented assistant that builds personalized checklists for caregivers preparing for medical visits. Based on the user’s request and context, generate a checklist that includes symptom tracking, medication list, family history, and questions. "
              "Include links to printable forms or online tools. Offer to send the checklist via SMS or email. Keep responses actionable and clear.")
    response = ("I’ve created a checklist for your mother’s appointment:\n\t• Recent medical records\n\t• Medication list (including supplements)\n\t• Symptom log\n\t• Family history (you can use https://cbiit.github.io/FHH/html/index.html)\n\t• Questions for the doctor\nWould you like me to send this checklist to your phone or email?")


def simulate_sample_conversation(user_utterance: str) -> list[AgentTurn]:
    """Return the static multi-agent simulation turns."""
    turns: list[AgentTurn] = []
    convo = logging.getLogger("conversation")
    convo.info("USER: %s", user_utterance)
    info_turn = AgentTurn(
        role="InfoAgent",
        prompt=SimpleInfoAgent.prompt,
        response=SimpleInfoAgent.response,
    )
    convo.info("InfoAgent PROMPT: %s", info_turn.prompt)
    convo.info("InfoAgent RESPONSE: %s", info_turn.response)
    turns.append(info_turn)

    context_turn = AgentTurn(
        role="PatientContextAgent",
        prompt=SimplePatientContextAgent.prompt,
        response=SimplePatientContextAgent.response,
    )
    convo.info("PatientContextAgent PROMPT: %s", context_turn.prompt)
    convo.info("PatientContextAgent RESPONSE: %s", context_turn.response)
    turns.append(context_turn)

    action_turn = AgentTurn(
        role="ActionAgent",
        prompt=SimpleActionAgent.prompt,
        response=SimpleActionAgent.response,
    )
    convo.info("ActionAgent PROMPT: %s", action_turn.prompt)
    convo.info("ActionAgent RESPONSE: %s", action_turn.response)
    turns.append(action_turn)

    return turns
