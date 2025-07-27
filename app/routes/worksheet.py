from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.worksheet_model import WorksheetRequest, WorksheetResponse, WorksheetType
from app.services.worksheet_generator_service import worksheet_generator_service
from app.services.session_service import session_service
from app.utils.logger import logger

router = APIRouter(
    prefix="/worksheets",
    tags=["Worksheets"],
    responses={404: {"description": "Not found"}},
)


@router.post("/generate", response_model=WorksheetResponse)
async def generate_worksheet(
    request: WorksheetRequest = Body(...),
    user_id: Optional[str] = Body(None, description="User ID for session tracking")
):
    """
    Generate an educational worksheet based on subject, grade, and topic.
    
    Request body should include:
    - **subject**: Subject for the worksheet (required)
    - **grade**: Grade level (required)
    - **topic**: Specific topic within the subject (required)
    - **worksheet_type**: Type of worksheet to generate (multiple_choice, fill_in_blanks, short_answers) (required)
    - **num_questions**: Number of questions to generate (default: 10)
    - **title**: Custom title for the worksheet (optional)
    - **include_answers**: Whether to include answer key (default: true)
    - **language**: Language for the worksheet content (default: "English")
    - **user_id**: Optional user ID for session tracking
    """
    try:
        # Variables to track session
        session_id = None
        
        # Check session if user_id is provided
        user_id_from_request = request.user_id or user_id
        if user_id_from_request:
            try:
                # Validate user session
                session = session_service.get_session(user_id_from_request)
                session_id = session.session_id
                logger.info(f"Using session {session_id} for user: {user_id_from_request}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                # Create a new session if user exists but has no session
                try:
                    session_id = session_service.create_session(user_id_from_request).session_id
                    logger.info(f"Created new session {session_id} for user: {user_id_from_request}")
                except Exception as create_error:
                    logger.error(f"Failed to create session: {create_error}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid user_id: {user_id_from_request}"
                    )
        
        # Validate worksheet type
        if request.worksheet_type not in [t for t in WorksheetType]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid worksheet_type. Must be one of: {', '.join([t.value for t in WorksheetType])}"
            )
        
        # Call service to generate worksheet
        result = await worksheet_generator_service.generate_worksheet(
            request=request,
            user_id=user_id_from_request
        )
        
        logger.info(f"Successfully generated {request.worksheet_type} worksheet for {request.subject}, grade {request.grade}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating worksheet: {e}")
        raise HTTPException(status_code=500, detail=f"Worksheet generation failed: {str(e)}")


@router.post("/generate-json", response_model=WorksheetResponse)
async def generate_worksheet_json(
    request: Dict[str, Any] = Body(...),
    user_id: Optional[str] = Body(None, description="User ID for session tracking")
):
    """
    Generate an educational worksheet based on subject, grade, and topic using a simplified JSON format.
    
    Request body should include:
    - **subject**: Subject for the worksheet (required)
    - **grade**: Grade level (required)
    - **topic**: Specific topic within the subject (required)
    - **worksheet_type**: Type of worksheet to generate (multiple_choice, fill_in_blanks, short_answers) (required)
    - **num_questions**: Number of questions to generate (default: 10)
    - **title**: Custom title for the worksheet (optional)
    - **include_answers**: Whether to include answer key (default: true)
    - **language**: Language for the worksheet content (default: "English")
    - **user_id**: Optional user ID for session tracking
    """
    try:
        # Variables to track session
        session_id = None
        
        # Extract user_id from request or param
        user_id_from_request = request.get("user_id", user_id)
        
        # Check session if user_id is provided
        if user_id_from_request:
            try:
                # Validate user session
                session = session_service.get_session(user_id_from_request)
                session_id = session.session_id
                logger.info(f"Using session {session_id} for user: {user_id_from_request}")
            except Exception as session_error:
                logger.warning(f"Invalid user_id for session: {session_error}")
                # Create a new session if user exists but has no session
                try:
                    session_id = session_service.create_session(user_id_from_request).session_id
                    logger.info(f"Created new session {session_id} for user: {user_id_from_request}")
                except Exception as create_error:
                    logger.error(f"Failed to create session: {create_error}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid user_id: {user_id_from_request}"
                    )
        
        # Extract parameters from request
        subject = request.get("subject")
        grade = request.get("grade")
        topic = request.get("topic")
        worksheet_type_str = request.get("worksheet_type", "multiple_choice")
        
        # Validate required fields
        if not subject:
            raise HTTPException(status_code=400, detail="Subject is required")
        if not grade:
            raise HTTPException(status_code=400, detail="Grade is required")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
            
        # Convert worksheet type string to enum
        try:
            worksheet_type = WorksheetType(worksheet_type_str)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid worksheet_type. Must be one of: {', '.join([t.value for t in WorksheetType])}"
            )
        
        # Create request object
        worksheet_request = WorksheetRequest(
            subject=subject,
            grade=grade,
            topic=topic,
            worksheet_type=worksheet_type,
            num_questions=request.get("num_questions", 10),
            title=request.get("title"),
            include_answers=request.get("include_answers", True),
            language=request.get("language", "English"),
            user_id=user_id_from_request
        )
        
        # Call service to generate worksheet
        result = await worksheet_generator_service.generate_worksheet(
            request=worksheet_request,
            user_id=user_id_from_request
        )
        
        logger.info(f"Successfully generated {worksheet_type.value} worksheet for {subject}, grade {grade}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating worksheet: {e}")
        raise HTTPException(status_code=500, detail=f"Worksheet generation failed: {str(e)}")

@router.get("/types", response_model=Dict[str, str])
async def get_worksheet_types():
    """
    Get available worksheet types and their descriptions.
    """
    return {
        WorksheetType.MULTIPLE_CHOICE.value: "Multiple choice questions with 4 options each",
        WorksheetType.FILL_IN_BLANKS.value: "Fill-in-the-blank questions with missing words",
        WorksheetType.SHORT_ANSWERS.value: "Short answer questions requiring brief written responses"
    }
