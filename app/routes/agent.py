from fastapi import APIRouter, HTTPException, Body
from app.models.agent_model import (
    MainAgentRequest, AgentResponse, HyperLocalContentRequest, VisualAidRequest,
    Language, ContentType, AgentType, Subject, HyperLocalContentResponse, VisualAidResponse, VisualAidType
)
from app.services.main_agent_service import main_agent_service
from app.services.hyper_local_content_service import hyper_local_content_service
from app.services.visual_aids_service import visual_aids_service
from app.services.session_service import session_service
from app.utils.logger import logger
from app.core.vertex_ai import VERTEX_AI_AVAILABLE, VERTEX_AI_INITIALIZED
from typing import Optional, List

router = APIRouter()

# Initialize services with error handling
try:
    # Services are already imported as singletons
    SERVICES_INITIALIZED = True
    logger.info("Agent services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agent services: {e}")
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
        logger.error(f"Error in enhanced hyper-local content generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-options")
async def get_content_options():
    """
    Get available options for content generation
    
    Returns:
        Dict: Available subjects, content types, languages, and other options
    """
    try:
        return {
            "subjects": [{"value": subject.value, "label": subject.value.replace("_", " ").title()} for subject in Subject],
            "content_types": [{"value": ct.value, "label": ct.value.replace("_", " ").title()} for ct in ContentType],
            "languages": [{"value": lang.value, "label": lang.value.title()} for lang in Language],
            "difficulty_levels": [
                {"value": "easy", "label": "Easy"},
                {"value": "medium", "label": "Medium"},
                {"value": "hard", "label": "Hard"}
            ],
            "content_lengths": [
                {"value": "short", "label": "Short"},
                {"value": "medium", "label": "Medium"},
                {"value": "long", "label": "Long"}
            ],
            "question_types": [
                {"value": "mcq", "label": "Multiple Choice Questions"},
                {"value": "short_answer", "label": "Short Answer Questions"},
                {"value": "long_answer", "label": "Long Answer Questions"}
            ],
            "grade_levels": list(range(1, 13)),
            "sample_locations": [
                "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", 
                "Hyderabad", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting content options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hyper-local-content", response_model=HyperLocalContentResponse)
async def generate_hyper_local_content(
    topic: str = Body(...),
    subject: Subject = Body(...),
    grade_levels: List[int] = Body(...),
    language: Language = Body(...),
    content_type: ContentType = Body(...),
    location: Optional[str] = Body("India"),
    cultural_context: Optional[str] = Body("Indian rural context"),
    include_local_examples: Optional[bool] = Body(True),
    include_cultural_context: Optional[bool] = Body(True),
    include_local_dialect: Optional[bool] = Body(False),
    include_regional_references: Optional[bool] = Body(True),
    include_local_currency: Optional[bool] = Body(True),
    include_local_festivals: Optional[bool] = Body(False),
    include_local_traditions: Optional[bool] = Body(False),
    difficulty_level: Optional[str] = Body("medium"),
    content_length: Optional[str] = Body("medium"),
    additional_requirements: Optional[str] = Body(None),
    include_questions: Optional[bool] = Body(False),
    question_types: Optional[List[str]] = Body([]),
    generate_preview: Optional[bool] = Body(True),
    preview_count: Optional[int] = Body(3),
    user_id: Optional[str] = Body(None)
):
    """
    Generate enhanced hyper-local, culturally relevant educational content
    
    Args:
        topic: The topic for content generation
        subject: The subject area
        grade_levels: Target grade levels (1-12)
        language: The language for content
        content_type: Type of content (story, word_problems, etc.)
        location: City/State/Region for local context
        cultural_context: Cultural context for content
        include_local_examples: Include local examples and references
        include_cultural_context: Include cultural traditions and festivals
        include_local_dialect: Include regional words with explanations
        include_regional_references: Include local geographical references
        include_local_currency: Use Indian currency in examples
        include_local_festivals: Include local festivals and celebrations
        include_local_traditions: Include local traditions and customs
        difficulty_level: Content difficulty (easy, medium, hard)
        content_length: Content length (short, medium, long)
        additional_requirements: Any additional requirements
        include_questions: Generate assessment questions
        question_types: Types of questions (mcq, short_answer, etc.)
        generate_preview: Generate multiple content pieces for preview
        preview_count: Number of content pieces to generate
        user_id: Optional user ID for session tracking and history
        
    Returns:
        HyperLocalContentResponse: The generated content with cultural elements
    """
    try:
        if not SERVICES_INITIALIZED or not hyper_local_content_service:
            raise HTTPException(status_code=503, detail="Agent services are not properly initialized")
        
        # Create request object
        request = HyperLocalContentRequest(
            topic=topic,
            subject=subject,
            grade_levels=grade_levels,
            language=language,
            content_type=content_type,
            location=location,
            cultural_context=cultural_context,
            include_local_examples=include_local_examples,
            include_cultural_context=include_cultural_context,
            include_local_dialect=include_local_dialect,
            include_regional_references=include_regional_references,
            include_local_currency=include_local_currency,
            include_local_festivals=include_local_festivals,
            include_local_traditions=include_local_traditions,
            difficulty_level=difficulty_level,
            content_length=content_length,
            additional_requirements=additional_requirements,
            include_questions=include_questions,
            question_types=question_types,
            generate_preview=generate_preview,
            preview_count=preview_count
        )
            
        logger.info(f"Received enhanced hyper-local content request for topic: {request.topic}")
        
        # Pass user_id for session tracking if provided
        response = hyper_local_content_service.generate_content(request, user_id=user_id)
        
        logger.info(f"Enhanced hyper-local content response status: {response.status}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating hyper-local content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/visual-aids", response_model=VisualAidResponse)
async def generate_visual_aid(
    description: str = Body(..., description="The description of what you want to generate as a visual aid"),
    subject: Subject = Body(..., description="The subject for which the visual aid is created"),
    topic: Optional[str] = Body(None, description="Optional topic - can be derived from description"),
    visual_type: Optional[VisualAidType] = Body(VisualAidType.LINE_DRAWING, description="Type of visual aid to generate"),
    grade_levels: Optional[List[int]] = Body([5, 6, 7], description="Target grade levels"),
    language: Optional[Language] = Body(Language.ENGLISH, description="Language for the visual aid"),
    complexity: Optional[str] = Body("medium", description="Complexity level (simple, medium, detailed)"),
    include_labels: Optional[bool] = Body(True, description="Include labels on the visual aid"),
    include_instructions: Optional[bool] = Body(True, description="Include teaching instructions"),
    blackboard_friendly: Optional[bool] = Body(True, description="Optimize for drawing on a blackboard"),
    color_scheme: Optional[str] = Body("blackboard", description="Color scheme (blackboard, colored, grayscale)"),
    additional_requirements: Optional[str] = Body(None, description="Any additional specifications"),
    user_id: Optional[str] = Body(None, description="User ID for session tracking")
):
    """
    Generate blackboard-friendly visual aids for educational use based on a text description
    
    This endpoint creates step-by-step instructions for drawing visual aids
    that teachers can reproduce on a blackboard or whiteboard to explain
    concepts effectively, primarily based on a text description.
    """
    try:
        # Check if services are initialized
        if not SERVICES_INITIALIZED or not visual_aids_service:
            raise HTTPException(
                status_code=503,
                detail="Visual aids service not initialized properly"
            )
        
        # If user_id is provided, validate it
        if user_id:
            try:
                session = session_service.get_session(user_id)
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {user_id}"
                )
        
        # Create request object
        request = VisualAidRequest(
            description=description,
            subject=subject,
            topic=topic,
            visual_type=visual_type,
            grade_levels=grade_levels,
            language=language,
            complexity=complexity,
            include_labels=include_labels,
            include_instructions=include_instructions,
            blackboard_friendly=blackboard_friendly,
            color_scheme=color_scheme,
            additional_requirements=additional_requirements,
            user_id=user_id
        )
        
        # Generate the visual aid
        response = visual_aids_service.generate_visual_aid(request, user_id=user_id)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating visual aid: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visual-aid-types")
async def get_visual_aid_types():
    """Get available visual aid types and their descriptions"""
    try:
        return {
            "visual_aid_types": [
                {
                    "type": VisualAidType.LINE_DRAWING.value,
                    "name": "Line Drawing",
                    "description": "Simple line drawings of concepts or objects",
                    "subjects": ["Science", "Environmental Science"]
                },
                {
                    "type": VisualAidType.CHART.value,
                    "name": "Chart",
                    "description": "Bar charts, pie charts, or other data representations",
                    "subjects": ["Mathematics", "Social Studies"]
                },
                {
                    "type": VisualAidType.DIAGRAM.value,
                    "name": "Diagram",
                    "description": "Labeled diagrams showing parts of a system or object",
                    "subjects": ["Science", "Social Studies"]
                },
                {
                    "type": VisualAidType.FLOWCHART.value,
                    "name": "Flowchart",
                    "description": "Step-by-step process or cycle visualizations",
                    "subjects": ["Science", "Social Studies", "General Knowledge"]
                },
                {
                    "type": VisualAidType.CONCEPT_MAP.value,
                    "name": "Concept Map",
                    "description": "Interconnected concepts with relationship indicators",
                    "subjects": ["All subjects"]
                },
                {
                    "type": VisualAidType.INFOGRAPHIC.value,
                    "name": "Infographic",
                    "description": "Information-rich visual representation of a topic",
                    "subjects": ["General Knowledge", "Social Studies"]
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving visual aid types: {e}")
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
                "/agent/test": "This test endpoint",
                "/agent/visual-aids-direct": "Direct image generation with Imagen 4"
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

@router.post("/visual-aids-direct", response_model=VisualAidResponse)
async def generate_visual_aid_direct(
    description: str = Body(..., embed=True),
    text: Optional[str] = Body(None, embed=True),
    user_id: Optional[str] = Body(None, embed=True, description="User ID for session tracking")
):
    """
    Direct endpoint for generating educational visual aids using Imagen 4
    
    Args:
        description: Description of the educational visual aid to generate
        text: Optional text to include in the visual
        
    Returns:
        VisualAidResponse containing image URL and drawing instructions
    """
    from app.core.vertex_ai import generate_image
    import os
    
    try:
        logger.info(f"Direct visual aid generation request: {description[:50]}...")
        
        # Check session if user_id is provided
        if user_id:
            try:
                # Validate user session
                session = session_service.get_session(user_id)
                logger.info(f"Using session for user: {user_id} in visual aids direct")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {user_id}"
                )
        
        # Prepare the prompt based on input
        prompt = description
        if text:
            prompt = f"{description} with the following text: {text}"
            
        # Create an enhanced educational prompt
        enhanced_prompt = f"""Create a clear, high-quality educational illustration about: {prompt}

Key requirements:
- Professional educational visual suitable for teaching
- Clear visual hierarchy and organization
- Accurate educational content
- Appropriate labeling of key elements
- Easy to understand at a glance
- Visually engaging for students
"""
        
        # Generate image using Vertex AI Imagen 4
        image_path = generate_image(enhanced_prompt)
        
        if not image_path:
            raise HTTPException(status_code=500, detail="Failed to generate visual aid")
            
        # Get relative path for the image URL
        relative_path = image_path.replace(os.getcwd(), "").lstrip("/")
        image_url = f"/static/{relative_path}" if not relative_path.startswith("static") else f"/{relative_path}"
        
        # Generate drawing instructions based on description
        instructions = f"Educational visualization of {description}"
        if text:
            instructions += f" including text: {text}"
            
        # Create visual aid response
        return VisualAidResponse(
            title=description[:50] + ("..." if len(description) > 50 else ""),
            description=description,
            image_url=image_url,
            image_path=image_path,
            drawing_instructions=instructions,
            teaching_tips=f"Use this visual to help students understand {description}.",
            visual_aid_type=VisualAidType.DIAGRAM
        )
        
    except Exception as e:
        logger.error(f"Error generating direct visual aid: {e}")
        raise HTTPException(status_code=500, detail=str(e))
