from fastapi import APIRouter, HTTPException, Body
from app.models.agent_model import (
    MainAgentRequest, AgentResponse, HyperLocalContentRequest,
    Language, ContentType, AgentType
)
from app.services.main_agent_service import MainAgentService
from app.services.hyper_local_content_service import HyperLocalContentService
from app.services.session_service import session_service
from app.utils.logger import logger
from typing import Optional, List

router = APIRouter()

# Initialize services with error handling
try:
    main_agent_service = MainAgentService()
    hyper_local_service = HyperLocalContentService()
    SERVICES_INITIALIZED = True
    logger.info("Agent services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agent services: {e}")
    main_agent_service = None
    hyper_local_service = None
    SERVICES_INITIALIZED = False

@router.post("/query", response_model=AgentResponse)
async def query_main_agent(request: MainAgentRequest):
    """
    Main endpoint for AI teaching assistant queries
    
    Returns:
        AgentResponse: The AI generated response along with session information
    """
    try:
        if not SERVICES_INITIALIZED or not main_agent_service:
            raise HTTPException(status_code=503, detail="Agent services are not properly initialized")
        
        # Validate user_id if provided
        if request.user_id is not None and not request.user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty if provided")
        
        logger.info(f"Received main agent query: {request.query[:100]}...")
        response = main_agent_service.process_request(request)
        logger.info(f"Main agent response status: {response.status}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in main agent query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hyper-local-content", response_model=AgentResponse)
async def generate_hyper_local_content(
    topic: str = Body(...),
    language: Language = Body(...),
    grade_levels: List[int] = Body([1, 2, 3, 4, 5]),
    cultural_context: str = Body("Indian rural context"),
    content_type: ContentType = Body(ContentType.STORY),
    subject: str = Body("general"),
    additional_requirements: Optional[str] = Body(None),
    user_id: Optional[str] = Body(None)
):
    """
    Generate hyper-local, culturally relevant educational content
    
    Args:
        topic: The topic for content generation
        language: The language for content
        grade_levels: Target grade levels (1-12)
        cultural_context: Cultural context for content
        content_type: Type of content (story, explanation, etc.)
        subject: Subject area (science, math, etc.)
        additional_requirements: Any additional requirements
        user_id: Optional user ID for session tracking and history
        
    Returns:
        AgentResponse: The generated content along with session information
    """
    try:
        if not SERVICES_INITIALIZED or not hyper_local_service:
            raise HTTPException(status_code=503, detail="Agent services are not properly initialized")
        
        # Create request object
        request = HyperLocalContentRequest(
            topic=topic,
            language=language,
            grade_levels=grade_levels,
            cultural_context=cultural_context,
            content_type=content_type,
            subject=subject,
            additional_requirements=additional_requirements
        )
            
        logger.info(f"Received hyper-local content request for topic: {request.topic}")
        
        # Pass user_id for session tracking if provided
        response = hyper_local_service.generate_content(request, user_id=user_id)
        
        logger.info(f"Hyper-local content response status: {response.status}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating hyper-local content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def agent_health_check():
    """Health check endpoint for agent services"""
    try:
        from app.core.vertex_ai import VERTEX_AI_AVAILABLE, VERTEX_AI_INITIALIZED
        
        status = "healthy"
        if not VERTEX_AI_AVAILABLE:
            status = "degraded - Vertex AI package not available"
        elif not VERTEX_AI_INITIALIZED:
            status = "degraded - Vertex AI not properly initialized"
        elif not SERVICES_INITIALIZED:
            status = "degraded - Agent services not initialized"
        
        return {
            "status": status,
            "service": "AI Teaching Assistant (Sahayak)",
            "services_initialized": SERVICES_INITIALIZED,
            "vertex_ai_available": VERTEX_AI_AVAILABLE,
            "vertex_ai_initialized": VERTEX_AI_INITIALIZED,
            "available_agents": [
                "main_agent",
                "hyper_local_content"
            ] if SERVICES_INITIALIZED else [],
            "supported_languages": [
                "english", "hindi", "marathi", "gujarati", "bengali",
                "tamil", "telugu", "kannada", "malayalam", "punjabi"
            ],
            "recommendations": [
                "Install google-cloud-aiplatform package" if not VERTEX_AI_AVAILABLE else None,
                "Configure Google Cloud credentials" if VERTEX_AI_AVAILABLE and not VERTEX_AI_INITIALIZED else None,
                "Enable Vertex AI API in Google Cloud Console" if VERTEX_AI_AVAILABLE and not VERTEX_AI_INITIALIZED else None
            ]
        }
    except Exception as e:
        logger.error(f"Error in agent health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_agent():
    """Test endpoint to verify agent functionality"""
    try:
        from app.core.vertex_ai import VERTEX_AI_AVAILABLE, VERTEX_AI_INITIALIZED
        
        return {
            "status": "success",
            "message": "Sahayak AI Teaching Assistant is ready to help teachers create engaging, culturally relevant educational content!",
            "services_status": {
                "services_initialized": SERVICES_INITIALIZED,
                "vertex_ai_available": VERTEX_AI_AVAILABLE,
                "vertex_ai_initialized": VERTEX_AI_INITIALIZED,
                "ready_for_production": SERVICES_INITIALIZED and VERTEX_AI_AVAILABLE and VERTEX_AI_INITIALIZED
            },
            "capabilities": [
                "Generate hyper-local stories in regional languages",
                "Create culturally relevant explanations",
                "Provide practical examples for multi-grade teaching",
                "Design resource-light classroom activities"
            ],
            "sample_queries": [
                "Create a story in Marathi about farmers to explain different soil types",
                "Explain photosynthesis using examples from Indian agriculture",
                "Generate an activity to teach counting using local objects"
            ],
            "endpoints": {
                "/agent/query": "Main agent endpoint for natural language queries",
                "/agent/hyper-local-content": "Direct endpoint for content generation",
                "/agent/health": "Service health status",
                "/agent/test": "This test endpoint"
            },
            "current_limitations": [
                "Vertex AI package not installed" if not VERTEX_AI_AVAILABLE else None,
                "Vertex AI not properly authenticated" if VERTEX_AI_AVAILABLE and not VERTEX_AI_INITIALIZED else None,
                "Agent services not initialized" if not SERVICES_INITIALIZED else None
            ]
        }
    except Exception as e:
        logger.error(f"Error in agent test: {e}")
        raise HTTPException(status_code=500, detail=str(e))
