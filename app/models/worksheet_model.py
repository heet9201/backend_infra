from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class WorksheetType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_BLANKS = "fill_in_blanks"
    SHORT_ANSWERS = "short_answers"


class WorksheetRequest(BaseModel):
    """Request model for worksheet generation."""
    subject: str = Field(..., description="Subject for the worksheet (e.g., Math, Science, History)")
    grade: str = Field(..., description="Grade level (e.g., '3', '5th', '8')")
    topic: str = Field(..., description="Specific topic within the subject")
    worksheet_type: WorksheetType = Field(..., description="Type of worksheet to generate")
    num_questions: int = Field(10, ge=5, le=30, description="Number of questions to generate (5-30)")
    title: Optional[str] = Field(None, description="Custom title for the worksheet")
    include_answers: bool = Field(True, description="Whether to include an answer key")
    language: str = Field("English", description="Language for the worksheet content")
    user_id: Optional[str] = Field(None, description="User ID for session tracking")


class WorksheetResponse(BaseModel):
    """Response model for worksheet generation."""
    pdf_url: str = Field(..., description="URL to the generated PDF worksheet")
    worksheet_type: WorksheetType = Field(..., description="Type of worksheet generated")
    subject: str = Field(..., description="Subject of the worksheet")
    grade: str = Field(..., description="Grade level")
    topic: str = Field(..., description="Specific topic")
    title: str = Field(..., description="Title of the worksheet")
    question_count: int = Field(..., description="Number of questions in the worksheet")
    session_id: Optional[str] = Field(None, description="Session ID if user provided a user_id")
