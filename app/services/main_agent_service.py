from app.models.agent_model import (
    MainAgentRequest, AgentResponse, AgentType, Language, 
    HyperLocalContentRequest, ContentType, SessionInfo
)
from app.core.vertex_ai import generate_educational_content
from app.utils.logger import logger
from app.utils.language_utils import LanguageDetector, detect_content_intent
from app.services.session_service import session_service
from typing import Dict, Any, List
import re
from datetime import datetime

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
            # Ensure we have a user ID for session management
            if not request.user_id:
                request.user_id = "anonymous"  # Fallback for users without ID
                logger.warning("Request without user_id, using anonymous ID")
            
            try:
                # Get session for the user (this will validate the user exists)
                user_session = session_service.get_session(request.user_id)
            except ValueError as e:
                # If user doesn't exist, return an error
                logger.error(f"User validation error: {e}")
                return AgentResponse(
                    status="error",
                    agent_type=AgentType.MAIN,
                    response="User authentication failed. Please register or login again.",
                    language=request.language,
                    error_message=str(e)
                )
            
            # Update session context with latest query
            if request.context:
                user_session.context.update(request.context)
            
            # Auto-detect language if not specified or if specified as English but query contains non-English
            detected_language = self.language_detector.detect_language(request.query)
            if request.language == Language.ENGLISH and detected_language != Language.ENGLISH:
                request.language = detected_language
                logger.info(f"Updated language from English to detected: {detected_language.value}")
                
            # Update session language preference
            user_session.language_preference = request.language.value
            
            agent_type = self.determine_agent_type(request.query)
            
            # Create a response based on agent type
            if agent_type == AgentType.HYPER_LOCAL_CONTENT:
                response = self._handle_hyper_local_content(request)
            else:
                response = self._handle_generic_response(request)
            
            # Add the interaction to the session history
            session_service.add_message(
                user_id=request.user_id,
                content=request.query,
                agent_type="user",
                metadata={"language": request.language.value}
            )
            
            # Add the agent response to the session history
            session_service.add_message(
                user_id=request.user_id,
                content=response.response,
                agent_type=response.agent_type.value,
                metadata={
                    "language": response.language.value,
                    "status": response.status,
                    **response.metadata
                }
            )
            
            # Add session information to the response
            session = user_session
            response.session = SessionInfo(
                session_id=session.session_id,
                user_id=session.user_id,
                language_preference=session.language_preference,
                message_count=len(session.messages),
                context_keys=list(session.context.keys()) if session.context else [],
                last_active=session.last_active.isoformat() if isinstance(session.last_active, datetime) else str(session.last_active)
            )
            
            return response
                
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
            
            # Pass user_id to generate_content for session tracking
            return hyper_local_service.generate_content(
                request=hyper_local_request,
                user_id=request.user_id
            )
            
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
            
            # Get user session for session info
            if request.user_id:
                user_session = session_service.get_session(request.user_id)
                
                response = AgentResponse(
                    status="success",
                    agent_type=AgentType.MAIN,
                    response=response_text,
                    language=request.language,
                    metadata={
                        "response_type": "generic_educational_assistance"
                    },
                    session=SessionInfo(
                        session_id=user_session.session_id,
                        user_id=user_session.user_id,
                        language_preference=user_session.language_preference,
                        message_count=len(user_session.messages),
                        context_keys=list(user_session.context.keys()) if user_session.context else [],
                        last_active=user_session.last_active.isoformat() if isinstance(user_session.last_active, datetime) else str(user_session.last_active)
                    )
                )
            else:
                response = AgentResponse(
                    status="success",
                    agent_type=AgentType.MAIN,
                    response=response_text,
                    language=request.language,
                    metadata={
                        "response_type": "generic_educational_assistance"
                    }
                )
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating generic response: {e}")
            
            # Include session info in error response if possible
            if request.user_id:
                try:
                    user_session = session_service.get_session(request.user_id)
                    return AgentResponse(
                        status="error",
                        agent_type=AgentType.MAIN,
                        response="I'm here to help you with educational content and teaching assistance. Could you please rephrase your request?",
                        language=request.language,
                        error_message=str(e),
                        session=SessionInfo(
                            session_id=user_session.session_id,
                            user_id=user_session.user_id,
                            language_preference=user_session.language_preference,
                            message_count=len(user_session.messages),
                            context_keys=list(user_session.context.keys()) if user_session.context else [],
                            last_active=user_session.last_active.isoformat() if isinstance(user_session.last_active, datetime) else str(user_session.last_active)
                        )
                    )
                except Exception as session_error:
                    logger.error(f"Error getting session info: {session_error}")
                    
            # Fallback response without session info
            return AgentResponse(
                status="error",
                agent_type=AgentType.MAIN,
                response="I'm here to help you with educational content and teaching assistance. Could you please rephrase your request?",
                language=request.language,
                error_message=str(e)
            )


# Create a singleton instance
main_agent_service = MainAgentService()
