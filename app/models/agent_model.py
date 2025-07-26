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
    WORD_PROBLEMS = "word_problems"
    READING_COMPREHENSION = "reading_comprehension"
    ACTIVITY_INSTRUCTIONS = "activity_instructions"
    STORIES_NARRATIVES = "stories_narratives"

class Subject(str, Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HINDI = "hindi"
    SOCIAL_STUDIES = "social_studies"
    ENVIRONMENTAL_SCIENCE = "environmental_science"
    GENERAL_KNOWLEDGE = "general_knowledge"
    MORAL_SCIENCE = "moral_science"
    ART_CRAFT = "art_craft"
    PHYSICAL_EDUCATION = "physical_education"

class AgentRequest(BaseModel):
    agent_type: AgentType
    query: str
    language: Optional[Language] = Language.ENGLISH
    context: Optional[Dict[str, Any]] = {}

class HyperLocalContentRequest(BaseModel):
    # Basic Information
    topic: str
    subject: Subject
    grade_levels: List[int]
    language: Language
    content_type: ContentType
    
    # Location and Cultural Context
    location: Optional[str] = "India"  # City/State/Region
    cultural_context: Optional[str] = "Indian rural context"
    
    # Additional Options
    include_local_examples: Optional[bool] = True
    include_cultural_context: Optional[bool] = True
    include_local_dialect: Optional[bool] = False
    include_regional_references: Optional[bool] = True
    include_local_currency: Optional[bool] = True
    include_local_festivals: Optional[bool] = False
    include_local_traditions: Optional[bool] = False
    
    # Content Specifications
    difficulty_level: Optional[str] = "medium"  # easy, medium, hard
    content_length: Optional[str] = "medium"  # short, medium, long
    additional_requirements: Optional[str] = None
    
    # Assessment Integration
    include_questions: Optional[bool] = False
    question_types: Optional[List[str]] = []  # mcq, short_answer, long_answer
    
    # Preview Options
    generate_preview: Optional[bool] = True
    preview_count: Optional[int] = 3  # Number of content pieces to generate

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

class ContentPiece(BaseModel):
    """Individual piece of generated content"""
    title: Optional[str] = None
    content: str
    content_type: ContentType
    local_elements: Optional[List[str]] = []  # Highlighted local elements
    cultural_annotations: Optional[List[str]] = []  # Cultural context notes
    difficulty_level: Optional[str] = None
    estimated_time: Optional[str] = None  # Estimated time to complete/read

class HyperLocalContentResponse(BaseModel):
    """Enhanced response for hyper-local content"""
    status: str
    agent_type: AgentType
    language: Language
    location: Optional[str] = None
    subject: Optional[str] = None
    grade_levels: Optional[List[int]] = []
    
    # Content pieces
    content_pieces: List[ContentPiece] = []
    
    # Questions/Assessment (if requested)
    questions: Optional[List[Dict[str, Any]]] = []
    
    # Cultural context information
    cultural_elements_used: Optional[List[str]] = []
    local_references: Optional[List[str]] = []
    dialect_terms: Optional[Dict[str, str]] = {}  # term: meaning
    
    # Generation metadata
    generation_time: Optional[str] = None
    content_quality_score: Optional[float] = None
    
    # Session and error info
    error_message: Optional[str] = None
    session: Optional[SessionInfo] = None
    metadata: Optional[Dict[str, Any]] = {}

class MainAgentRequest(BaseModel):
    query: str
    language: Optional[Language] = Language.ENGLISH
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
