from fastapi import APIRouter, HTTPException, Body
from app.core.vertex_ai import generate_image
from app.utils.logger import logger
from typing import Optional
from pydantic import BaseModel
import os
from app.services.session_service import session_service

router = APIRouter()

class VisualAidRequest(BaseModel):
    description: str
    text: Optional[str] = None
    user_id: Optional[str] = None

class VisualAidResponse(BaseModel):
    image_path: str
    drawing_instructions: str

@router.post("/visual-aids", response_model=VisualAidResponse)
async def create_visual_aid(request: VisualAidRequest = Body(...)):
    """
    Generate an educational image based on description and text.
    
    Args:
        request: Contains description (required) and text (optional)
        
    Returns:
        VisualAidResponse: Contains path to generated image and drawing instructions
    """
    try:
        logger.info(f"Visual aid generation request received for: {request.description[:50]}...")
        
        # Check session if user_id is provided
        if request.user_id:
            try:
                # Validate user session
                session = session_service.get_session(request.user_id)
                logger.info(f"Using session for user: {request.user_id}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid user_id: {request.user_id}"
                )
        
        # Prepare the prompt based on input
        prompt = request.description
        if request.text:
            # Combine description and text for better context
            prompt = f"{request.description} with the following text: {request.text}"
        
        # Generate image using Vertex AI
        image_path = generate_image(prompt)
        
        if not image_path:
            raise HTTPException(status_code=500, detail="Failed to generate visual aid")
        
        # Create drawing instructions based on description
        drawing_instructions = f"Educational visualization of {request.description}"
        if request.text:
            drawing_instructions += f" including the text: {request.text}"
        
        # Create response with relative path
        # Convert absolute path to relative path for API response
        relative_path = os.path.relpath(image_path, os.getcwd())
        
        return VisualAidResponse(
            image_path=relative_path,
            drawing_instructions=drawing_instructions
        )
        
    except Exception as e:
        logger.error(f"Error generating visual aid: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating visual aid: {str(e)}")
