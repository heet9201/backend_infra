from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import base64
from io import BytesIO

from app.models.content_generation_model import (
    ContentType, OutputFormat, ResearchDepth, ContentLength, 
    ContentGenerationRequest, ContentGenerationResponse
)
from app.services.content_generation_service import content_generation_service
from app.utils.logger import logger

router = APIRouter(
    prefix="/content",
    tags=["content"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    file: UploadFile = File(...),
    content_type: ContentType = Form(...),
    output_format: OutputFormat = Form(...),
    research_depth: ResearchDepth = Form(...),
    content_length: ContentLength = Form(...),
    local_language: Optional[str] = Form("english")
):
    """
    Generate educational content from an uploaded image or PDF file based on specified parameters.
    
    - **file**: The image or PDF file to process
    - **content_type**: Type of content to generate (detailed_content, summary, key_points, etc.)
    - **output_format**: Format of the output content (text, bullet_points, q&a_format, etc.)
    - **research_depth**: Depth of research to perform (surface, basic, moderate, etc.)
    - **content_length**: Length of content to generate (concise, brief, moderate, etc.)
    - **local_language**: Language for the generated content (default: English)
    """
    try:
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
            result = await content_generation_service.process_image(file_content, settings)
        else:  # pdf
            result = await content_generation_service.process_pdf(file_content, settings)
        
        logger.info(f"Successfully generated {content_type.value} content in {output_format.value} format")
        return result
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@router.post("/generate-from-base64", response_model=ContentGenerationResponse)
async def generate_content_from_base64(
    file_data: str,
    file_type: str,  # "image" or "pdf"
    content_type: ContentType,
    output_format: OutputFormat,
    research_depth: ResearchDepth,
    content_length: ContentLength,
    local_language: Optional[str] = "English"
):
    """
    Generate educational content from a base64-encoded image or PDF file.
    
    - **file_data**: Base64-encoded image or PDF data
    - **file_type**: Type of file ("image" or "pdf")
    - **content_type**: Type of content to generate
    - **output_format**: Format of the output content
    - **research_depth**: Depth of research to perform
    - **content_length**: Length of content to generate
    - **local_language**: Language for the generated content (default: English)
    """
    try:
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
            result = await content_generation_service.process_image(file_content, settings)
        else:  # pdf
            result = await content_generation_service.process_pdf(file_content, settings)
        
        logger.info(f"Successfully generated {content_type.value} content in {output_format.value} format from base64 data")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content from base64: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")
