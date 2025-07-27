from enum import Enum
from typing import Optional, Union, List
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    DETAILED_CONTENT = "detailed_content"
    SUMMARY = "summary"
    KEY_POINTS = "key_points"
    STUDY_GUIDE = "study_guide"
    PRACTICE_QUESTIONS = "practice_questions"


class OutputFormat(str, Enum):
    TEXT = "text"
    BULLET_POINTS = "bullet_points"
    QA_FORMAT = "qa_format"
    MIND_MAP = "mind_map"
    FLASHCARDS = "flashcards"


class ResearchDepth(str, Enum):
    SURFACE = "surface"
    BASIC = "basic"
    MODERATE = "moderate"
    DETAILED = "detailed"
    DEEP = "deep"


class ContentLength(str, Enum):
    CONCISE = "concise"
    BRIEF = "brief"
    MODERATE = "moderate"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ContentGenerationRequest(BaseModel):
    """Request model for content generation from image or PDF."""
    content_type: ContentType = Field(
        ..., description="Type of content to generate")
    output_format: OutputFormat = Field(
        ..., description="Format of the output content")
    research_depth: ResearchDepth = Field(
        ..., description="Depth of research to perform")
    content_length: ContentLength = Field(
        ..., description="Length of content to generate")
    local_language: str = Field(
        default="English", description="Language for the generated content")


class ContentGenerationResponse(BaseModel):
    """Response model for content generation."""
    content: str = Field(..., description="Generated content")
    language: str = Field(..., description="Language of the generated content")
    content_type: ContentType = Field(..., description="Type of content generated")
    output_format: OutputFormat = Field(..., description="Format of the output content")
    source_type: str = Field(..., description="Type of source (image or PDF)")
    additional_resources: Optional[List[str]] = Field(
        None, description="Additional resources or references")
    session_id: Optional[str] = Field(
        None, description="Session ID if user provided a user_id")
    user_id: Optional[str] = Field(
        None, description="User ID if provided")
