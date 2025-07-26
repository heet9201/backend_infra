from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from app.services.session_service import session_service
from app.models.session_model import (
    SessionResponse, UserMessage, SessionHistoryRequest, 
    SessionHistoryResponse, SessionDetailsResponse
)
from app.utils.logger import logger
from typing import List, Optional
from datetime import datetime

router = APIRouter()

@router.get("/history/{user_id}", response_model=List[UserMessage])
async def get_user_history(user_id: str, limit: Optional[int] = Query(10, ge=1, le=100)):
    """Get user message history"""
    try:
        # Check if the user exists (for non-anonymous users)
        if user_id != "anonymous" and not session_service.user_exists(user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        messages = session_service.get_user_history(user_id, limit)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear/{user_id}", response_model=SessionResponse)
async def clear_user_session(user_id: str):
    """Clear a user's session history"""
    try:
        # Check if the user exists (for non-anonymous users)
        if user_id != "anonymous" and not session_service.user_exists(user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        response = session_service.clear_session(user_id)
        if response.status == "error":
            raise HTTPException(status_code=500, detail=response.message)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing user session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{user_id}", response_model=SessionDetailsResponse)
async def get_session_info(user_id: str):
    """Get information about a user's session"""
    try:
        # Check if the user exists (for non-anonymous users)
        if user_id != "anonymous" and not session_service.user_exists(user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        return session_service.get_session_details(user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/all/{user_id}", response_model=List[str])
async def get_all_sessions(user_id: str):
    """Get all session IDs for a user"""
    try:
        # Check if the user exists (for non-anonymous users)
        if user_id != "anonymous" and not session_service.user_exists(user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        sessions = session_service.get_all_sessions_for_user(user_id)
        return sessions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting all sessions for user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/by-id", response_model=SessionHistoryResponse)
async def get_session_by_id(request: SessionHistoryRequest):
    """
    Get session history by session ID and user ID
    
    This endpoint allows retrieving a specific session by its ID and validates that it belongs to the user.
    """
    try:
        if not request.session_id or not request.user_id:
            raise HTTPException(status_code=400, detail="Session ID and User ID are required")
            
        # Check if the user exists (for non-anonymous users)
        if request.user_id != "anonymous" and not session_service.user_exists(request.user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {request.user_id} not found")
        
        session_history = session_service.get_session_history(
            session_id=request.session_id,
            user_id=request.user_id,
            limit=request.limit
        )
        
        if not session_history:
            raise HTTPException(
                status_code=404, 
                detail=f"Session not found or does not belong to user {request.user_id}"
            )
        
        return session_history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-id/{session_id}/{user_id}", response_model=SessionHistoryResponse)
async def get_session_by_id_path(
    session_id: str = Path(..., description="The ID of the session to retrieve"),
    user_id: str = Path(..., description="The ID of the user who owns the session"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return")
):
    """
    Get session history by session ID and user ID (URL path parameters)
    
    This endpoint allows retrieving a specific session by its ID and validates that it belongs to the user.
    """
    try:
        # Check if the user exists (for non-anonymous users)
        if user_id != "anonymous" and not session_service.user_exists(user_id):
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        session_history = session_service.get_session_history(
            session_id=session_id,
            user_id=user_id,
            limit=limit
        )
        
        if not session_history:
            raise HTTPException(
                status_code=404, 
                detail=f"Session not found or does not belong to user {user_id}"
            )
        
        return session_history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session by ID: {e}")
        raise HTTPException(status_code=500, detail=str(e))
            
@router.get("/info/{user_id}")
async def get_session_info_old_version(user_id: str):
    """Get information about a user's session (old version, kept for compatibility)"""
    try:
        session = session_service.get_session(user_id)
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "language_preference": session.language_preference,
            "message_count": len(session.messages),
            "context_keys": list(session.context.keys()) if session.context else []
        }
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
