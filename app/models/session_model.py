from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID

class UserMessage(BaseModel):
    """Represents a single message in a conversation"""
    timestamp: datetime
    content: str
    agent_type: str
    metadata: Optional[Dict[str, Any]] = {}

class UserSession(BaseModel):
    """Represents a user session"""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    messages: List[UserMessage] = []
    language_preference: Optional[str] = "english"
    context: Dict[str, Any] = {}

class SessionResponse(BaseModel):
    """Response model for session operations"""
    status: str
    session_id: str
    message: Optional[str] = None
    
class SessionHistoryRequest(BaseModel):
    """Request model for retrieving session history"""
    session_id: str
    user_id: str
    limit: Optional[int] = Field(default=50, ge=1, le=100)
    
class SessionHistoryResponse(BaseModel):
    """Response model for session history"""
    status: str
    session_id: str
    user_id: str
    created_at: Optional[str] = None  # ISO format datetime
    last_active: Optional[str] = None  # ISO format datetime
    language_preference: Optional[str] = None
    message_count: int
    messages: List[UserMessage]
    context_keys: Optional[List[str]] = []
    
class SessionDetailsResponse(BaseModel):
    """Response model with session details but no messages"""
    status: str
    session_id: str
    user_id: str
    created_at: Optional[str] = None  # ISO format datetime
    last_active: Optional[str] = None  # ISO format datetime
    language_preference: Optional[str] = None
    message_count: int
    context_keys: Optional[List[str]] = []
