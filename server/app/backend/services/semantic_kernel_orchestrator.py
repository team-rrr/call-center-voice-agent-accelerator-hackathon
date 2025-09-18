"""
Semantic Kernel Multi-Agent Orchestrator Service for healthcare appointment preparation.
Parallel implementation using Microsoft Semantic Kernel for advanced AI orchestration.
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Try to import Semantic Kernel with v1.x API
try:
    import semantic_kernel as sk
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
    from semantic_kernel.connectors.ai import PromptExecutionSettings
    from semantic_kernel.functions import KernelArguments
    SEMANTIC_KERNEL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Semantic Kernel library not available: {e}")
    sk = None
    SEMANTIC_KERNEL_AVAILABLE = False


class SemanticKernelMultiAgentOrchestratorService:
    """
    Advanced multi-agent orchestrator using Microsoft Semantic Kernel.
    Provides same interface as SimpleMultiAgentOrchestratorService but with SK capabilities.
    """
    
    def __init__(self):
        self.kernel = None
        self.chat_service = None
        self._semantic_kernel_available = False
        self._initialized = False
        
        # Agent function references
        self.info_agent_function = None
        self.patient_context_function = None
        self.action_agent_function = None
        self.synthesis_function = None
        
    async def initialize(self):
        """Initialize Semantic Kernel with Azure OpenAI."""
        if not SEMANTIC_KERNEL_AVAILABLE:
            logger.error("Semantic Kernel library not available")
            self._semantic_kernel_available = False
            return
            
        try:
            self._semantic_kernel_available = True
            
            # Get Azure OpenAI configuration from existing env vars
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_VOICE_LIVE_API_KEY")  # Reuse existing key
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
            
            if not endpoint:
                logger.error("AZURE_OPENAI_ENDPOINT not configured")
                self._semantic_kernel_available = False
                return
                
            if not api_key:
                logger.error("AZURE_VOICE_LIVE_API_KEY not configured")
                self._semantic_kernel_available = False
                return
            
            # Store configuration
            self.endpoint = endpoint
            self.api_key = api_key
            self.deployment_name = deployment_name
            self.api_version = api_version
            
            logger.info(f"Initializing Semantic Kernel Multi-Agent Orchestrator with endpoint: {endpoint}")
            logger.info(f"Using deployment: {deployment_name}, API version: {api_version}")
            
            # Create Semantic Kernel instance
            self.kernel = sk.Kernel()
            
            # Add Azure OpenAI chat completion service with v1.x API
            service_id = "azure_openai_chat"
            self.chat_service = AzureChatCompletion(
                service_id=service_id,
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            self.kernel.add_service(self.chat_service)
            
            # Register our healthcare agent functions
            await self._register_agent_functions()
            
            # Test the connection
            test_result = await self.kernel.invoke_prompt("Hello, test connection")
            
            if test_result:
                logger.info("Semantic Kernel connection test successful")
                self._initialized = True
            
            logger.info("SemanticKernelMultiAgentOrchestratorService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SemanticKernelMultiAgentOrchestratorService: {e}")
            self._semantic_kernel_available = False
    
    async def _register_agent_functions(self):
        """Register healthcare agent functions with Semantic Kernel using v1.x API."""
        
        # InfoAgent Function
        info_agent_template = """You are a helpful assistant that provides caregivers with guidance on preparing for medical appointments. 

When asked about what to bring to medical visits, respond with a clear, friendly checklist that includes:
- Medical history and records
- Current medication list (including supplements)
- Symptom log or notes
- Family medical history if relevant
- Questions for the healthcare provider
- Insurance information and ID
- Previous test results
- Comfort items for waiting

User question: {{$user_message}}

Provide practical, caring advice as if you're helping a family member prepare."""

        self.info_agent_function = self.kernel.add_function(
            function_name="InfoAgent",
            plugin_name="HealthcareAgents",
            prompt=info_agent_template,
            prompt_execution_settings=PromptExecutionSettings(
                service_id="azure_openai_chat",
                max_tokens=400,
                temperature=0.7
            )
        )
        
        # PatientContextAgent Function
        patient_context_template = """You are a patient context specialist. Based on this patient's medical profile, provide specific guidance for their upcoming appointment.

Patient Profile:
- Age: {{$patient_age}}
- Medical Conditions: {{$patient_conditions}}
- Current Medications: {{$patient_medications}}
- Known Allergies: {{$patient_allergies}}
- Recent Tests: {{$patient_recent_tests}}
- Appointment Type: {{$appointment_type}}

User is asking: {{$user_message}}

Provide patient-specific advice considering their conditions, medications, and medical history. Focus on what's most important for someone with their specific health profile."""

        self.patient_context_function = self.kernel.add_function(
            function_name="PatientContextAgent",
            plugin_name="HealthcareAgents",
            prompt=patient_context_template,
            prompt_execution_settings=PromptExecutionSettings(
                service_id="azure_openai_chat",
                max_tokens=500,
                temperature=0.6
            )
        )
        
        # ActionAgent Function
        action_agent_template = """You are an action-oriented assistant that creates specific, actionable checklists for medical appointment preparation.

For the request: "{{$user_message}}"

Create a detailed checklist with specific action items. Format as a clear numbered or bulleted list. Include:

1. Documents to gather
2. Information to prepare
3. Items to bring
4. Questions to write down
5. Logistics to arrange
6. Follow-up actions

Make each item specific and actionable. Focus on practical steps they can take right now to be fully prepared."""

        self.action_agent_function = self.kernel.add_function(
            function_name="ActionAgent", 
            plugin_name="HealthcareAgents",
            prompt=action_agent_template,
            prompt_execution_settings=PromptExecutionSettings(
                service_id="azure_openai_chat",
                max_tokens=600,
                temperature=0.7
            )
        )
        
        # Synthesis Function
        synthesis_template = """You are a helpful healthcare assistant speaking to a caregiver. Create a warm, conversational response that feels natural and supportive.

Caregiver's Question: "{{$user_message}}"

Information Available:
---
General Healthcare Guidance:
{{$info_text}}

Patient-Specific Context:
{{$patient_text}}

Recommended Actions & Checklist:
{{$action_text}}
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

        self.synthesis_function = self.kernel.add_function(
            function_name="ResponseSynthesis",
            plugin_name="HealthcareAgents", 
            prompt=synthesis_template,
            prompt_execution_settings=PromptExecutionSettings(
                service_id="azure_openai_chat",
                max_tokens=900,
                temperature=0.7
            )
        )
    
    async def call_orchestrator(self, user_message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main orchestrator method that coordinates all three agents using Semantic Kernel.
        """
        if not self._initialized or not self._semantic_kernel_available:
            await self.initialize()
            
        if not self._initialized:
            return {
                "success": False,
                "error": "Semantic Kernel orchestrator not properly initialized",
                "response": "I'm having trouble connecting to the AI service. Please try again later."
            }
            
        logger.info(f"Processing Semantic Kernel orchestrator request: {user_message[:100]}...")
        
        try:
            # Get mock patient data (Phase 2A will enhance this)
            mock_patient_data = self._get_mock_patient_data()
            
            # Prepare arguments for agent functions using KernelArguments
            info_args = KernelArguments(user_message=user_message)
            
            patient_args = KernelArguments(
                user_message=user_message,
                patient_age=str(mock_patient_data['age']),
                patient_conditions=', '.join(mock_patient_data['conditions']),
                patient_medications=', '.join(mock_patient_data['medications']),
                patient_allergies=', '.join(mock_patient_data['allergies']),
                patient_recent_tests=', '.join(mock_patient_data['recent_tests']),
                appointment_type=mock_patient_data['upcoming_appointment']
            )
            
            action_args = KernelArguments(user_message=user_message)
            
            # Call all three agents in parallel using Semantic Kernel
            info_task = self.kernel.invoke(self.info_agent_function, info_args)
            patient_task = self.kernel.invoke(self.patient_context_function, patient_args)
            action_task = self.kernel.invoke(self.action_agent_function, action_args)
            
            # Wait for all agents to complete
            info_result, patient_result, action_result = await asyncio.gather(
                info_task, patient_task, action_task
            )
            
            # Extract text from results
            info_text = str(info_result).strip()
            patient_text = str(patient_result).strip()
            action_text = str(action_result).strip()
            
            # Synthesize the responses using Semantic Kernel
            synthesis_args = KernelArguments(
                user_message=user_message,
                info_text=info_text,
                patient_text=patient_text,
                action_text=action_text
            )
            
            synthesis_result = await self.kernel.invoke(self.synthesis_function, synthesis_args)
            synthesized_response = str(synthesis_result).strip()
            
            # Enhance the synthesized response
            enhanced_response = self._enhance_response_quality(synthesized_response, user_message)
            
            # Create structured response
            structured_response = {
                "response_text": enhanced_response,
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
                "response": enhanced_response,
                "structured_data": structured_response,
                "session_id": session_id,
                "orchestrator_type": "semantic_kernel"
            }
            
        except Exception as e:
            logger.error(f"Error in Semantic Kernel multi-agent orchestrator: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble processing your appointment preparation request. Please try again later."
            }
    
    def _get_mock_patient_data(self) -> Dict[str, Any]:
        """Get mock patient data - will be enhanced in Phase 2A."""
        return {
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
    
    def _extract_checklist(self, action_text: str) -> List[str]:
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
    
    def _extract_links(self, text: str) -> List[str]:
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
    
    def _extract_follow_up_actions(self, action_text: str) -> List[str]:
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
        if self.kernel:
            # Semantic Kernel doesn't require explicit cleanup in current version
            pass


# Global instance
_semantic_kernel_orchestrator_service = None

async def get_semantic_kernel_orchestrator_service() -> SemanticKernelMultiAgentOrchestratorService:
    """Get the global Semantic Kernel multi-agent orchestrator service instance."""
    global _semantic_kernel_orchestrator_service
    
    if _semantic_kernel_orchestrator_service is None:
        _semantic_kernel_orchestrator_service = SemanticKernelMultiAgentOrchestratorService()
        await _semantic_kernel_orchestrator_service.initialize()
    
    return _semantic_kernel_orchestrator_service