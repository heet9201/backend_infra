from fastapi import APIRouter, HTTPException, Body, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import base64
import json

from app.models.content_generation_model import (
    ContentType, OutputFormat, ResearchDepth, ContentLength, 
    ContentGenerationRequest, ContentGenerationResponse
)
from app.services.content_generation_service import content_generation_service
from app.services.session_service import session_service
from app.utils.logger import logger

from app.models.agent_model import AgentType

router = APIRouter(
    prefix="/agent/content",
    tags=["Content Analysis"],
    responses={404: {"description": "Not found"}},
)

# Additional router for simplified content endpoints
content_router = APIRouter(
    prefix="/content",
    tags=["Content Generation"],
    responses={404: {"description": "Not found"}},
)

def _get_optimal_settings_for_content_type(content_type: ContentType) -> Dict[str, Any]:
    """
    Get optimal default settings for a specific content type.
    
    Args:
        content_type: The type of content being generated
        
    Returns:
        Dict with suggested defaults for output_format, research_depth, and content_length
    """
    # Define optimal defaults for different content types
    content_type_defaults = {
        ContentType.DETAILED_CONTENT: {
            "output_format": OutputFormat.TEXT,
            "research_depth": ResearchDepth.DETAILED,
            "content_length": ContentLength.COMPREHENSIVE
        },
        ContentType.SUMMARY: {
            "output_format": OutputFormat.TEXT,
            "research_depth": ResearchDepth.MODERATE,
            "content_length": ContentLength.CONCISE
        },
        ContentType.KEY_POINTS: {
            "output_format": OutputFormat.BULLET_POINTS,
            "research_depth": ResearchDepth.MODERATE,
            "content_length": ContentLength.BRIEF
        },
        ContentType.STUDY_GUIDE: {
            "output_format": OutputFormat.QA_FORMAT,
            "research_depth": ResearchDepth.DETAILED,
            "content_length": ContentLength.DETAILED
        },
        ContentType.PRACTICE_QUESTIONS: {
            "output_format": OutputFormat.QA_FORMAT,
            "research_depth": ResearchDepth.MODERATE,
            "content_length": ContentLength.MODERATE
        }
    }
    
    # Return defaults for the specified content type, or general defaults if not found
    return content_type_defaults.get(content_type, {
        "output_format": OutputFormat.TEXT,
        "research_depth": ResearchDepth.MODERATE,
        "content_length": ContentLength.MODERATE
    })

@router.post("/analyze", response_model=ContentGenerationResponse)
async def analyze_content(
    file: UploadFile = File(...),
    content_type: ContentType = Form(...),
    output_format: OutputFormat = Form(...),
    research_depth: ResearchDepth = Form(...),
    content_length: ContentLength = Form(...),
    local_language: Optional[str] = Form("English"),
    agent_type: Optional[AgentType] = Form(AgentType.MAIN),
    user_id: Optional[str] = Form(None, description="User ID for session tracking")
):
    """
    Analyze an image or PDF document and generate educational content based on specified parameters.
    This endpoint is designed to be used with the main agent interface.
    
    - **file**: The image or PDF file to process
    - **content_type**: Type of content to generate (detailed_content, summary, key_points, etc.)
    - **output_format**: Format of the output content (text, bullet_points, q&a_format, etc.)
    - **research_depth**: Depth of research to perform (surface, basic, moderate, etc.)
    - **content_length**: Length of content to generate (concise, brief, moderate, etc.)
    - **local_language**: Language for the generated content (default: English)
    - **agent_type**: Type of agent to use (default: MAIN)
    """
    try:
        # Variables to track session
        session_id = None
        
        # Check session if user_id is provided
        if user_id:
            try:
                # Validate user session
                session = session_service.get_session(user_id)
                session_id = session.session_id
                logger.info(f"Using session {session_id} for user: {user_id}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {user_id}"
                )
        
        # Validate file type
        content_type_header = file.content_type.lower()
        if "image" in content_type_header:
            file_type = "image"
        elif "pdf" in content_type_header or file.filename.lower().endswith(".pdf"):
            file_type = "pdf"
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload an image or PDF."
            )
        
        # Read file content
        file_content = await file.read()
        
        # Get default settings based on content type
        # For form submission we use the provided parameters, but also log the optimal settings
        default_settings = _get_optimal_settings_for_content_type(content_type)
        
        # Check if any parameters differ from optimal settings and log it
        if (output_format != default_settings.get("output_format") or
            research_depth != default_settings.get("research_depth") or
            content_length != default_settings.get("content_length")):
            logger.info(f"Custom settings used for {content_type.value}: " +
                       f"format={output_format}, depth={research_depth}, length={content_length}")
        
        # Create settings object
        settings = ContentGenerationRequest(
            content_type=content_type,
            output_format=output_format,
            research_depth=research_depth,
            content_length=content_length,
            local_language=local_language
        )
        
        # Process file based on type
        if file_type == "image":
            result = await content_generation_service.process_image(file_content, settings, user_id, session_id)
        else:  # pdf
            result = await content_generation_service.process_pdf(file_content, settings, user_id, session_id)
        
        logger.info(f"Successfully analyzed {file_type} and generated {content_type.value} content")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.post("/analyze-json", response_model=ContentGenerationResponse)
async def analyze_content_json(
    request: Dict[str, Any] = Body(...),
    user_id: Optional[str] = Body(None, description="User ID for session tracking")
):
    """
    Generate Q&A content from an image or PDF document provided as base64-encoded data.
    This endpoint accepts a JSON body with minimal parameters.
    
    Request body should include:
    - **file_data**: Base64-encoded file data (required)
    - **file_type**: "image" or "pdf" (required)
    - **local_language**: Language for the generated content (default: "English")
    - **user_id**: Optional user ID for session tracking
    """
    try:
        # Variables to track session
        session_id = None
        
        # Check session if user_id is provided
        user_id_from_request = request.get("user_id", user_id)
        if user_id_from_request:
            try:
                # Validate user session
                session = session_service.get_session(user_id_from_request)
                session_id = session.session_id
                logger.info(f"Using session {session_id} for user: {user_id_from_request}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {user_id_from_request}"
                )
        
        # Extract parameters from request
        file_data = request.get("file_data")
        file_type = request.get("file_type")
        
        # Check for required parameters
        if not file_data or not file_type:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: file_data and file_type are required"
            )
        
        # Validate file type
        if file_type not in ["image", "pdf"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file_type. Must be 'image' or 'pdf'."
            )
        
        # Decode base64 data
        try:
            # Remove data URL prefix if present
            if "base64," in file_data:
                file_data = file_data.split("base64,")[1]
            
            file_content = base64.b64decode(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # Create simplified settings object
        settings = ContentGenerationRequest(
            content_type=ContentType.STUDY_GUIDE,
            output_format=OutputFormat.QA_FORMAT,
            research_depth=ResearchDepth.MODERATE,
            content_length=ContentLength.MODERATE,
            local_language=request.get("local_language", "English")
        )
        
        # Process file based on type
        if file_type == "image":
            result = await content_generation_service.process_image(file_content, settings, user_id_from_request, session_id)
        else:  # pdf
            result = await content_generation_service.process_pdf(file_content, settings, user_id_from_request, session_id)
        
        logger.info(f"Successfully generated Q&A content from {file_type}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing content from JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")
        
@router.post("/analyze-base64", response_model=ContentGenerationResponse)
async def analyze_content_base64(
    request: Dict[str, Any] = Body(...),
    user_id: Optional[str] = Body(None, description="User ID for session tracking")
):
    """
    Analyze a base64-encoded image or PDF and generate educational content.
    This endpoint accepts a JSON body with all parameters.
    
    Request body should include:
    - **file_data**: Base64-encoded file data
    - **file_type**: "image" or "pdf"
    - **content_type**: Type of content to generate
    - **output_format**: Format of the output content
    - **research_depth**: Depth of research to perform
    - **content_length**: Length of content to generate
    - **local_language**: Language for the generated content (default: "English")
    """
    try:
        # Variables to track session
        session_id = None
        
        # Check session if user_id is provided
        user_id_from_request = request.get("user_id", user_id)
        if user_id_from_request:
            try:
                # Validate user session
                session = session_service.get_session(user_id_from_request)
                session_id = session.session_id
                logger.info(f"Using session {session_id} for user: {user_id_from_request}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {user_id_from_request}"
                )
        
        # Extract parameters from request
        file_data = request.get("file_data")
        file_type = request.get("file_type")
        
        if not file_data or not file_type:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: file_data and file_type"
            )
        
        # Validate file type
        if file_type not in ["image", "pdf"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file_type. Must be 'image' or 'pdf'."
            )
        
        # Decode base64 data
        try:
            # Remove data URL prefix if present
            if "base64," in file_data:
                file_data = file_data.split("base64,")[1]
            
            file_content = base64.b64decode(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # Get content type
        content_type_val = request.get("content_type", ContentType.DETAILED_CONTENT)
        
        # Get optimal settings based on content type
        default_settings = _get_optimal_settings_for_content_type(content_type_val)
        
        # Create settings object using defaults when parameters aren't specified
        settings = ContentGenerationRequest(
            content_type=content_type_val,
            output_format=request.get("output_format", default_settings.get("output_format")),
            research_depth=request.get("research_depth", default_settings.get("research_depth")),
            content_length=request.get("content_length", default_settings.get("content_length")),
            local_language=request.get("local_language", "English")
        )
        
        # Process file based on type
        if file_type == "image":
            result = await content_generation_service.process_image(file_content, settings, user_id_from_request, session_id)
        else:  # pdf
            result = await content_generation_service.process_pdf(file_content, settings, user_id_from_request, session_id)
        
        logger.info(f"Successfully analyzed base64 {file_type} and generated content")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing base64 content: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

# Simplified content generation endpoint using Vertex AI directly
@content_router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: Dict[str, Any] = Body(...)
):
    """
    Generate content from an image or PDF document provided as base64-encoded data.
    This endpoint uses Vertex AI directly for both text extraction and content generation.
    
    Request body should include:
    - **file_data**: Base64-encoded file data (required)
    - **file_type**: "image" or "pdf" (required)
    - **output_format**: "q&a_format" (Q&A format) or "bullet_points" (default: "q&a_format")
    - **language**: Language for the generated content (default: "English")
    - **user_id**: Optional user ID for session tracking
    """
    try:
        # Import directly here to ensure it's loaded
        from app.core.vertex_ai import (
            extract_text_from_image_with_vertex,
            extract_text_from_pdf_with_vertex,
            generate_content
        )
        
        # Extract parameters from request
        file_data = request.get("file_data")
        file_type = request.get("file_type")
        output_format = request.get("output_format", "q&a_format")
        language = request.get("language", "English")
        user_id = request.get("user_id")
        session_id = None
        
        # Check for required parameters
        if not file_data or not file_type:
            raise HTTPException(
                status_code=400,
                detail="Missing required parameters: file_data and file_type are required"
            )
        
        # Validate file type
        if file_type not in ["image", "pdf"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file_type. Must be 'image' or 'pdf'."
            )
        
        # Decode base64 data
        try:
            # Remove data URL prefix if present
            if "base64," in file_data:
                file_data = file_data.split("base64,")[1]
            
            file_content = base64.b64decode(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        # Handle session tracking if user_id is provided
        if user_id:
            try:
                # Get or create session for the user
                try:
                    session = session_service.get_session(user_id)
                    session_id = session.session_id
                    logger.info(f"Using existing session {session_id} for user: {user_id}")
                except ValueError as val_error:
                    # User might not exist, create an anonymous session
                    logger.warning(f"User validation failed: {val_error}. Creating anonymous session.")
                    session = session_service.create_session("anonymous")
                    session_id = session.session_id
                    user_id = "anonymous"  # Reset user_id to anonymous
                
                # Update session context with content generation details
                context_update = {
                    "last_content_generation": {
                        "timestamp": datetime.now().isoformat(),
                        "source_type": file_type,
                        "output_format": output_format,
                        "language": language
                    }
                }
                
                # Update session with content generation activity
                session_service.update_session_context(session_id, context_update)
                logger.info(f"Updated session {session_id} with content generation context")
                
            except Exception as session_error:
                logger.warning(f"Session tracking error: {session_error}")
                session_id = None  # Continue without session
                
        # Extract text directly with Vertex AI
        logger.info(f"Extracting text from {file_type} using Vertex AI")
        if file_type == "image":
            extracted_text = extract_text_from_image_with_vertex(file_content)
            source_type = "image"
        else:  # pdf
            extracted_text = extract_text_from_pdf_with_vertex(file_content)
            source_type = "pdf"
        
        # Validate output format
        if output_format not in ["q&a_format", "bullet_points"]:
            logger.warning(f"Invalid output_format: {output_format}. Using default: q&a_format")
            output_format = "q&a_format"
        
        # Generate content based on the requested output format
        if output_format == "q&a_format":
            # Generate Q&A content
            prompt = f"""
You are an educational content expert. Create a set of questions and answers based on the following text.
Focus on the key concepts and important details. 

Your response should start with the introduction: "Here is a Q&A based on the content:" and then continue with the questions and answers.

Format your response as:

Here is a Q&A based on the content:

Q1: [Question]
A1: [Answer]

Q2: [Question]
A2: [Answer]

And so on. Create 3-5 high-quality questions that test understanding of the material.
Make the answers detailed and informative. Use language that is clear and appropriate for students.

Language: {language}

TEXT TO ANALYZE:
{extracted_text}
"""
            logger.info("Generating Q&A content with Vertex AI")
            vertex_output_format = OutputFormat.QA_FORMAT
            
        else:  # bullet_points
            # Generate bullet point summary
            prompt = f"""
You are an educational content expert. Create a comprehensive summary of the key points from the following text.
Focus on the main concepts, important details, and key takeaways.

Your response should start with the introduction: "Here is a summary of the content:" and then continue with bullet points.

Format your response as:

Here is a summary of the content:

• [Main point 1]
• [Main point 2]
  • [Sub-point 2.1]
  • [Sub-point 2.2]
• [Main point 3]

And so on. Create a well-organized summary with 5-10 bullet points highlighting the most important information.
Use clear and concise language that is appropriate for students.

Language: {language}

TEXT TO ANALYZE:
{extracted_text}
"""
            logger.info("Generating bullet point summary with Vertex AI")
            vertex_output_format = OutputFormat.BULLET_POINTS
        
        # Generate content using Vertex AI directly
        generated_content = generate_content(prompt, temperature=0.2)
        
        # Create response object with session information
        result = ContentGenerationResponse(
            content=generated_content,
            language=language,
            content_type=ContentType.STUDY_GUIDE,
            output_format=vertex_output_format,
            source_type=source_type,
            additional_resources=None,
            session_id=session_id,
            user_id=user_id
        )
        
        # Log session information if available
        if session_id:
            logger.info(f"Content generated with session tracking: user_id={user_id}, session_id={session_id}")
        
        logger.info(f"Successfully generated content from {file_type} via /content/generate endpoint using Vertex AI directly")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
