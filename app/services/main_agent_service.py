from app.models.agent_model import (
    MainAgentRequest, AgentResponse, AgentType, Language, 
    HyperLocalContentRequest, ContentType
)
from app.core.vertex_ai import generate_educational_content
from app.utils.logger import logger
from app.utils.language_utils import LanguageDetector, detect_content_intent
from typing import Dict, Any
import re

class MainAgentService:
    """Main agent that routes requests to specialized agents"""
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.agent_keywords = {
            AgentType.HYPER_LOCAL_CONTENT: [
                'story', 'create', 'generate', 'content', 'local', 'cultural',
                'farmers', 'rural', 'village', 'explain', 'teach about',
                'कहानी', 'कथा', 'વાર્તા', 'গল্প', 'கதை', 'కథ', 'ಕಥೆ', 'കഥ', 'ਕਹਾਣੀ'
            ]
        }
    
    def determine_agent_type(self, query: str) -> AgentType:
        """Determine which agent should handle the request based on query analysis"""
        query_lower = query.lower()
        
        # Check for hyper-local content keywords
        for keyword in self.agent_keywords[AgentType.HYPER_LOCAL_CONTENT]:
            if keyword in query_lower:
                return AgentType.HYPER_LOCAL_CONTENT
        
        # Default to hyper-local content for now
        return AgentType.HYPER_LOCAL_CONTENT
    
    def extract_topic_from_query(self, query: str) -> str:
        """Extract the main topic from the query"""
        # Simple topic extraction - can be enhanced with NLP
        patterns = [
            r'about\s+([^.!?]+)',
            r'explain\s+([^.!?]+)',
            r'teach\s+about\s+([^.!?]+)',
            r'create.*story.*about\s+([^.!?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, return a portion of the query
        words = query.split()
        if len(words) > 3:
            return ' '.join(words[-5:])  # Last 5 words as topic
        return query
    
    def process_request(self, request: MainAgentRequest) -> AgentResponse:
        """Process the main agent request and route to appropriate specialized agent"""
        try:
            # Auto-detect language if not specified or if specified as English but query contains non-English
            detected_language = self.language_detector.detect_language(request.query)
            if request.language == Language.ENGLISH and detected_language != Language.ENGLISH:
                request.language = detected_language
                logger.info(f"Updated language from English to detected: {detected_language.value}")
            
            agent_type = self.determine_agent_type(request.query)
            
            if agent_type == AgentType.HYPER_LOCAL_CONTENT:
                return self._handle_hyper_local_content(request)
            else:
                return self._handle_generic_response(request)
                
        except Exception as e:
            logger.error(f"Error processing main agent request: {e}")
            return AgentResponse(
                status="error",
                agent_type=AgentType.MAIN,
                response="I apologize, but I encountered an error while processing your request. Please try again.",
                language=request.language,
                error_message=str(e)
            )
    
    def _handle_hyper_local_content(self, request: MainAgentRequest) -> AgentResponse:
        """Handle hyper-local content generation requests"""
        try:
            # Extract topic and intent from query
            topic = self.extract_topic_from_query(request.query)
            intent_data = detect_content_intent(request.query)
            
            # Create hyper-local content request
            hyper_local_request = HyperLocalContentRequest(
                topic=topic,
                language=request.language,
                grade_levels=intent_data.get("grade_levels", [1, 2, 3, 4, 5]),
                cultural_context="Indian rural context",
                content_type=ContentType(intent_data.get("content_type", "story")),
                subject=intent_data.get("subject", "general"),
                additional_requirements=None
            )
            
            # Use hyper-local content service
            from app.services.hyper_local_content_service import HyperLocalContentService
            hyper_local_service = HyperLocalContentService()
            
            return hyper_local_service.generate_content(hyper_local_request)
            
        except Exception as e:
            logger.error(f"Error handling hyper-local content: {e}")
            return self._handle_generic_response(request)
    
    def _handle_generic_response(self, request: MainAgentRequest) -> AgentResponse:
        """Handle generic requests that don't fit specific agent types"""
        try:
            # Create a generic educational prompt
            prompt = f"""As a teaching assistant for Indian teachers, please help with this request: {request.query}
            
            Please provide a helpful response that:
            - Is appropriate for multi-grade classrooms
            - Uses simple, clear language
            - Includes practical teaching suggestions
            - Considers resource constraints in Indian schools"""
            
            response_text = generate_educational_content(prompt, request.language.value)
            
            return AgentResponse(
                status="success",
                agent_type=AgentType.MAIN,
                response=response_text,
                language=request.language,
                metadata={
                    "response_type": "generic_educational_assistance"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating generic response: {e}")
            return AgentResponse(
                status="error",
                agent_type=AgentType.MAIN,
                response="I'm here to help you with educational content and teaching assistance. Could you please rephrase your request?",
                language=request.language,
                error_message=str(e)
            )
