from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

class AgentType(str, Enum):
    MAIN = "main"
    HYPER_LOCAL_CONTENT = "hyper_local_content"
    DIFFERENTIATED_MATERIALS = "differentiated_materials"
    KNOWLEDGE_BASE = "knowledge_base"
    VISUAL_AIDS = "visual_aids"

class Language(str, Enum):
    ENGLISH = "english"
    HINDI = "hindi"
    MARATHI = "marathi"
    GUJARATI = "gujarati"
    BENGALI = "bengali"
    TAMIL = "tamil"
    TELUGU = "telugu"
    KANNADA = "kannada"
    MALAYALAM = "malayalam"
    PUNJABI = "punjabi"

class ContentType(str, Enum):
    STORY = "story"
    EXPLANATION = "explanation"
    EXAMPLE = "example"
    ACTIVITY = "activity"
    WORKSHEET = "worksheet"
    LESSON_PLAN = "lesson_plan"

class AgentRequest(BaseModel):
    agent_type: AgentType
    query: str
    language: Optional[Language] = Language.ENGLISH
    context: Optional[Dict[str, Any]] = {}

class HyperLocalContentRequest(BaseModel):
    topic: str
    language: Language
    grade_levels: Optional[List[int]] = [1, 2, 3, 4, 5]
    cultural_context: Optional[str] = "Indian rural context"
    content_type: ContentType = ContentType.STORY
    subject: Optional[str] = "general"
    additional_requirements: Optional[str] = None

class SessionInfo(BaseModel):
    """Session information included in responses"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    language_preference: Optional[str] = None
    message_count: Optional[int] = None
    context_keys: Optional[List[str]] = None
    last_active: Optional[str] = None  # ISO format date string

class AgentResponse(BaseModel):
    status: str
    agent_type: AgentType
    response: str
    language: Language
    metadata: Optional[Dict[str, Any]] = {}
    error_message: Optional[str] = None
    session: Optional[SessionInfo] = None

class MainAgentRequest(BaseModel):
    query: str
    language: Optional[Language] = Language.ENGLISH
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
