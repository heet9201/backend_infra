from fastapi import APIRouter, HTTPException
from app.models.agent_model import (
    MainAgentRequest, AgentResponse, HyperLocalContentRequest
)
from app.services.main_agent_service import MainAgentService
from app.services.hyper_local_content_service import HyperLocalContentService
from app.utils.logger import logger

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
    """Main endpoint for AI teaching assistant queries"""
    try:
        if not SERVICES_INITIALIZED or not main_agent_service:
            raise HTTPException(status_code=503, detail="Agent services are not properly initialized")
            
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
async def generate_hyper_local_content(request: HyperLocalContentRequest):
    """Generate hyper-local, culturally relevant educational content"""
    try:
        if not SERVICES_INITIALIZED or not hyper_local_service:
            raise HTTPException(status_code=503, detail="Agent services are not properly initialized")
            
        logger.info(f"Received hyper-local content request for topic: {request.topic}")
        response = hyper_local_service.generate_content(request)
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
