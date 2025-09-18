"""
Simple Multi-Agent Orchestrator Service for healthcare appointment preparation.
Uses basic Azure OpenAI calls instead of complex Semantic Kernel features.
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import OpenAI for direct API calls
try:
    from openai import AsyncAzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenAI library not available: {e}")
    AsyncAzureOpenAI = None
    OPENAI_AVAILABLE = False


class SimpleMultiAgentOrchestratorService:
    """
    Simple multi-agent orchestrator that coordinates healthcare agents.
    Uses direct Azure OpenAI calls instead of Semantic Kernel for simplicity.
    """
    
    def __init__(self):
        self.client = None
        self._openai_available = False
        self._initialized = False
        
    async def initialize(self):
        """Initialize Azure OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI library not available")
            self._openai_available = False
            return
            
        try:
            self._openai_available = True
            
            # Get Azure OpenAI configuration from existing env vars
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_VOICE_LIVE_API_KEY")  # Reuse existing key
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")  # Use more standard API version
            
            if not endpoint:
                logger.error("AZURE_OPENAI_ENDPOINT not configured")
                self._openai_available = False
                return
                
            if not api_key:
                logger.error("AZURE_VOICE_LIVE_API_KEY not configured")
                self._openai_available = False
                return
            
            # Store configuration
            self.endpoint = endpoint
            self.api_key = api_key
            self.deployment_name = deployment_name
            self.api_version = api_version
            
            logger.info(f"Initializing Simple Multi-Agent Orchestrator with endpoint: {endpoint}")
            logger.info(f"Using deployment: {deployment_name}, API version: {api_version}")
            
            # Create Azure OpenAI client
            self.client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            # Test the connection
            test_response = await self.client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            if test_response:
                logger.info("Azure OpenAI connection test successful")
                self._initialized = True
            
            logger.info("SimpleMultiAgentOrchestratorService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SimpleMultiAgentOrchestratorService: {e}")
            self._openai_available = False
    
    async def call_orchestrator(self, user_message: str, session_id: str = None) -> Dict[str, Any]:
        """
        Main orchestrator method that coordinates all three agents.
        """
        if not self._initialized or not self._openai_available:
            await self.initialize()
            
        if not self._initialized:
            return {
                "success": False,
                "error": "Orchestrator not properly initialized",
                "response": "I'm having trouble connecting to the AI service. Please try again later."
            }
            
        logger.info(f"Processing orchestrator request: {user_message[:100]}...")
        
        try:
            # Call all three agents in parallel for efficiency
            info_task = self._call_info_agent(user_message)
            patient_task = self._call_patient_context_agent(user_message)
            action_task = self._call_action_agent(user_message)
            
            # Wait for all agents to complete
            info_text, patient_text, action_text = await asyncio.gather(
                info_task, patient_task, action_task
            )
            
            # Synthesize the responses into a coherent final response
            synthesized_response = await self._synthesize_response(
                user_message, info_text, patient_text, action_text
            )
            
            # Create structured response
            structured_response = {
                "response_text": synthesized_response,
                "agent_responses": {
                    "info_agent": info_text,
                    "patient_context": patient_text,
                    "action_agent": action_text
                },
                "checklist": self._extract_checklist(action_text),
                "links": self._extract_links(info_text + action_text),
                "follow_up_actions": self._extract_follow_up_actions(action_text)
            }
            
            return {
                "success": True,
                "response": synthesized_response,
                "structured_data": structured_response,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in simple multi-agent orchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble processing your appointment preparation request. Please try again later."
            }
    
    async def _call_info_agent(self, user_message: str) -> str:
        """Call the InfoAgent for general appointment guidance."""
        try:
            prompt = f"""You are a helpful assistant that provides caregivers with guidance on preparing for medical appointments. 

When asked about what to bring to medical visits, respond with a clear, friendly checklist that includes:
- Medical history and records
- Current medication list (including supplements)
- Symptom log or notes
- Family medical history if relevant
- Questions for the healthcare provider
- Insurance information and ID
- Previous test results
- Comfort items for waiting

User question: {user_message}

Provide practical, caring advice as if you're helping a family member prepare."""

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"InfoAgent error: {e}")
            return "General appointment preparation guidance not available at this time."
    
    async def _call_patient_context_agent(self, user_message: str) -> str:
        """Call the PatientContextAgent for patient-specific context."""
        try:
            # Mock patient data - this will be enhanced in Phase 2A
            mock_patient_data = {
                "name": "Patient (Mother)",
                "age": 72,
                "conditions": ["Hypertension", "Atrial Fibrillation"],
                "medications": [
                    "Metoprolol 50mg twice daily",
                    "Warfarin 5mg daily",
                    "Lisinopril 10mg daily"
                ],
                "allergies": ["Penicillin"],
                "recent_tests": [
                    "ECG (3 months ago) - showing controlled AFib",
                    "Blood pressure monitoring - averaging 140/85"
                ],
                "upcoming_appointment": "Cardiology follow-up"
            }
            
            prompt = f"""You are a patient context specialist. Based on this patient's medical profile, provide specific guidance for their upcoming appointment.

Patient Profile:
- Age: {mock_patient_data['age']}
- Medical Conditions: {', '.join(mock_patient_data['conditions'])}
- Current Medications: {', '.join(mock_patient_data['medications'])}
- Known Allergies: {', '.join(mock_patient_data['allergies'])}
- Recent Tests: {', '.join(mock_patient_data['recent_tests'])}
- Appointment Type: {mock_patient_data['upcoming_appointment']}

User is asking: {user_message}

Provide patient-specific advice considering their conditions, medications, and medical history. Focus on what's most important for someone with their specific health profile."""

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"PatientContextAgent error: {e}")
            return "Patient-specific context not available at this time."
    
    async def _call_action_agent(self, user_message: str) -> str:
        """Call the ActionAgent for specific action items and checklists."""
        try:
            prompt = f"""You are an action-oriented assistant that creates specific, actionable checklists for medical appointment preparation.

For the request: "{user_message}"

Create a detailed checklist with specific action items. Format as a clear numbered or bulleted list. Include:

1. Documents to gather
2. Information to prepare
3. Items to bring
4. Questions to write down
5. Logistics to arrange
6. Follow-up actions

Make each item specific and actionable. Focus on practical steps they can take right now to be fully prepared."""

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"ActionAgent error: {e}")
            return "Action checklist not available at this time."

    async def _synthesize_response(self, user_message: str, info_text: str, patient_text: str, action_text: str) -> str:
        """Synthesize all agent responses into a coherent final response with enhanced quality."""
        try:
            # Detect conversation type for appropriate tone
            conversation_type = self._detect_conversation_type(user_message)
            
            synthesis_prompt = f"""You are a helpful healthcare assistant speaking to a caregiver. Create a warm, conversational response that feels natural and supportive.

Caregiver's Question: "{user_message}"

Information Available:
---
General Healthcare Guidance:
{info_text}

Patient-Specific Context:
{patient_text}

Recommended Actions & Checklist:
{action_text}
---

Guidelines for your response:
1. Start with a warm, understanding acknowledgment of their situation
2. Provide a clear, direct answer to their question
3. Naturally weave in relevant patient-specific details
4. Present action items as helpful suggestions, not commands
5. End with reassurance and offer of continued support
6. Use a conversational, caring tone throughout
7. Avoid medical jargon - use plain, accessible language
8. Keep the response concise but comprehensive (aim for 150-250 words)

Create a single, flowing response that sounds like a knowledgeable friend helping them prepare."""

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": synthesis_prompt}],
                max_tokens=900,
                temperature=0.7
            )
            
            synthesized_response = response.choices[0].message.content.strip()
            
            # Validate and enhance the synthesized response
            return self._enhance_response_quality(synthesized_response, user_message)
            
        except Exception as e:
            logger.error(f"Response synthesis error: {e}")
            # Enhanced fallback with better formatting
            return self._create_fallback_response(user_message, info_text, patient_text, action_text)
    
    def _detect_conversation_type(self, user_message: str) -> str:
        """Detect the type of conversation to adjust tone appropriately."""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['worried', 'concerned', 'scared', 'anxious']):
            return 'concerned'
        elif any(word in message_lower for word in ['first time', 'new', 'never', 'don\'t know']):
            return 'inexperienced'
        elif any(word in message_lower for word in ['emergency', 'urgent', 'immediately']):
            return 'urgent'
        else:
            return 'standard'
    
    def _enhance_response_quality(self, response: str, user_message: str) -> str:
        """Enhance response quality with final touches."""
        # Ensure response doesn't start with generic phrases
        generic_starts = ["Based on the information", "According to", "Here is"]
        for generic in generic_starts:
            if response.startswith(generic):
                # Find the first sentence and make it more personal
                sentences = response.split('. ')
                if len(sentences) > 1:
                    response = '. '.join(sentences[1:])
                break
        
        # Ensure response ends with a supportive note if it doesn't already
        supportive_endings = ['support', 'help', 'questions', 'here for you', 'assistance']
        if not any(ending in response.lower() for ending in supportive_endings):
            response += " Feel free to reach out if you have any other questions!"
        
        return response
    
    def _create_fallback_response(self, user_message: str, info_text: str, patient_text: str, action_text: str) -> str:
        """Create a well-formatted fallback response when synthesis fails."""
        fallback = f"I understand you're preparing for an important appointment. Here's what I can help you with:\n\n"
        
        if info_text and len(info_text.strip()) > 0:
            fallback += f"**General Guidance:**\n{info_text}\n\n"
        
        if patient_text and len(patient_text.strip()) > 0:
            fallback += f"**For Your Mother's Specific Situation:**\n{patient_text}\n\n"
        
        if action_text and len(action_text.strip()) > 0:
            fallback += f"**Action Steps:**\n{action_text}\n\n"
        
        fallback += "I hope this helps you feel more prepared. Please let me know if you need any clarification!"
        
        return fallback
    
    def _extract_checklist(self, action_text: str) -> list:
        """Extract checklist items from action agent response with enhanced pattern recognition."""
        lines = action_text.split('\n')
        checklist = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or ':' in line and len(line.split()) <= 4:
                continue
            
            # Enhanced pattern matching for various list formats
            checklist_item = None
            
            # Bullet points (-, •, *, ►)
            if line.startswith(('- ', '• ', '* ', '► ')):
                checklist_item = line[2:].strip()
            
            # Numbered lists (1., 2., etc.)
            elif any(line.startswith(f'{i}.') for i in range(1, 100)):
                checklist_item = '. '.join(line.split('.')[1:]).strip()
            
            # Bracketed numbers [1], [2], etc.
            elif line.startswith('[') and ']' in line:
                checklist_item = line[line.find(']')+1:].strip()
            
            # Parenthetical numbers (1), (2), etc.
            elif line.startswith('(') and ')' in line:
                checklist_item = line[line.find(')')+1:].strip()
            
            # Items that start with action verbs
            elif any(line.lower().startswith(verb) for verb in ['bring', 'take', 'pack', 'prepare', 'gather', 'collect', 'organize']):
                checklist_item = line
            
            # Clean up and add valid items
            if checklist_item and len(checklist_item.strip()) > 3:
                # Remove trailing punctuation and clean up
                checklist_item = checklist_item.rstrip('.,;')
                if checklist_item not in checklist:  # Avoid duplicates
                    checklist.append(checklist_item)
        
        return checklist
    
    def _extract_links(self, text: str) -> list:
        """Extract URLs from agent responses with validation and context."""
        import re
        
        # Enhanced regex for URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        # Add some common healthcare resource URLs if none found
        if not urls:
            # Add contextual links based on content
            text_lower = text.lower()
            contextual_links = []
            
            if 'cardiology' in text_lower or 'heart' in text_lower:
                contextual_links.append('https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/appointments-and-questions-for-your-doctor')
            
            if 'medication' in text_lower or 'prescription' in text_lower:
                contextual_links.append('https://www.fda.gov/drugs/ensuring-safe-use-medicine/taking-medicine-safely')
            
            if 'insurance' in text_lower:
                contextual_links.append('https://www.healthcare.gov/using-marketplace-coverage/')
            
            urls.extend(contextual_links)
        
        # Remove duplicates and validate
        unique_urls = []
        for url in urls:
            if url not in unique_urls and len(url) > 10:  # Basic validation
                unique_urls.append(url)
        
        return unique_urls[:3]  # Limit to 3 most relevant links
    
    def _extract_follow_up_actions(self, action_text: str) -> list:
        """Extract follow-up actions from action agent response with intelligent detection."""
        actions = []
        text_lower = action_text.lower()
        
        # Communication actions
        if any(word in text_lower for word in ['send', 'share', 'email', 'text', 'sms']):
            if 'checklist' in text_lower or 'list' in text_lower:
                actions.append('Send checklist to phone/email')
            else:
                actions.append('Share information with family')
        
        # Reminder actions  
        if any(word in text_lower for word in ['remind', 'reminder', 'alert', 'notification']):
            if 'appointment' in text_lower:
                actions.append('Set appointment reminder')
            elif 'medication' in text_lower:
                actions.append('Set medication reminder')
            else:
                actions.append('Set general reminder')
        
        # Follow-up care
        if any(phrase in text_lower for phrase in ['follow up', 'follow-up', 'next visit', 'next appointment']):
            actions.append('Schedule follow-up appointment')
        
        # Preparation actions
        if any(word in text_lower for word in ['prepare', 'organize', 'gather', 'collect']):
            actions.append('Organize materials before appointment')
        
        # Transportation/logistics
        if any(word in text_lower for word in ['transport', 'drive', 'parking', 'arrive']):
            actions.append('Plan transportation and arrival')
        
        # Contact actions
        if any(word in text_lower for word in ['call', 'contact', 'reach out']):
            if 'doctor' in text_lower or 'office' in text_lower:
                actions.append('Contact healthcare provider if needed')
            else:
                actions.append('Make necessary phone calls')
        
        # Remove duplicates while preserving order
        unique_actions = []
        for action in actions:
            if action not in unique_actions:
                unique_actions.append(action)
        
        return unique_actions[:4]  # Limit to 4 most relevant actions
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.close()


# Global instance
_orchestrator_service = None

async def get_orchestrator_service() -> SimpleMultiAgentOrchestratorService:
    """Get the global simple multi-agent orchestrator service instance."""
    global _orchestrator_service
    
    if _orchestrator_service is None:
        _orchestrator_service = SimpleMultiAgentOrchestratorService()
        await _orchestrator_service.initialize()
    
    return _orchestrator_service