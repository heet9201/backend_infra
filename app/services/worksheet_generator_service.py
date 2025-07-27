import os
import uuid
import time
import base64
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import json

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Google Cloud
from google import genai
from google.genai import types

# Project imports
from app.models.worksheet_model import WorksheetType, WorksheetRequest, WorksheetResponse
from app.services.session_service import session_service
from app.utils.logger import logger


class WorksheetGeneratorService:
    """Service for generating educational worksheets based on subject, grade, and topic."""
    
    def __init__(self):
        # Create directories for storing generated PDFs
        self.pdf_dir = os.path.join(os.getcwd(), "generated_pdfs")
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Initialize Google AI client for RAG
        self._init_genai_client()
        
        # Worksheet type prompts to guide generation
        self._worksheet_type_prompts = {
            WorksheetType.MULTIPLE_CHOICE: {
                "instruction": "Create a multiple choice worksheet with {num_questions} questions and 4 options each.",
                "format": "The questions should be in standard multiple choice format with options A, B, C, and D.",
                "example": "1. What is the capital of France?\nA) London\nB) Paris\nC) Berlin\nD) Rome"
            },
            WorksheetType.FILL_IN_BLANKS: {
                "instruction": "Create a fill-in-the-blanks worksheet with {num_questions} questions.",
                "format": "Each question should have a blank indicated by underscores (____) where a word or phrase should be filled in.",
                "example": "1. The process of plants making food using sunlight is called ____."
            },
            WorksheetType.SHORT_ANSWERS: {
                "instruction": "Create a short answer worksheet with {num_questions} questions.",
                "format": "Each question should require a brief response of 1-3 sentences.",
                "example": "1. Explain how photosynthesis works in plants."
            }
        }
    
    def _init_genai_client(self):
        """Initialize the Google AI Generative client."""
        try:
            # Set up the client with project and location
            self.genai_client = genai.Client(
                vertexai=True,
                project="purva-api",
                location="global",
            )
            self.model_name = "gemini-2.5-flash-lite"
            logger.info("Google Generative AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Generative AI client: {e}")
            self.genai_client = None
    
    async def generate_worksheet(self, 
                                request: WorksheetRequest,
                                user_id: Optional[str] = None) -> WorksheetResponse:
        """Generate a worksheet based on the provided parameters."""
        try:
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
                    # Create a new session for this user
                    try:
                        session_id = session_service.create_session(user_id)
                        logger.info(f"Created new session {session_id} for user: {user_id}")
                    except Exception as create_error:
                        logger.error(f"Failed to create session: {create_error}")
            
            # Retrieve content from RAG based on subject, grade, topic
            rag_content = self._retrieve_rag_content(
                subject=request.subject,
                grade=request.grade,
                topic=request.topic,
                worksheet_type=request.worksheet_type,
                num_questions=request.num_questions,
                language=request.language
            )
            
            if not rag_content:
                raise Exception("Failed to retrieve content from RAG system")
            
            # Generate worksheet content using the RAG response
            worksheet_content = self._process_rag_response(
                rag_content, 
                request.worksheet_type, 
                include_answers=request.include_answers
            )
            
            # Generate PDF from content
            pdf_path, pdf_url = self._generate_pdf(
                worksheet_content=worksheet_content,
                request=request
            )
            
            # Update session with worksheet information if session exists
            if session_id and user_id:
                metadata = {
                    "worksheet_type": request.worksheet_type,
                    "subject": request.subject,
                    "grade": request.grade,
                    "topic": request.topic,
                    "pdf_url": pdf_url,
                    "timestamp": datetime.now().isoformat()
                }
                
                try:
                    session_service.add_message(
                        user_id=user_id,
                        content=f"Generated {request.worksheet_type} worksheet for {request.subject}, grade {request.grade}, topic: {request.topic}",
                        agent_type="worksheet_generator",
                        metadata=metadata
                    )
                    logger.info(f"Updated session {session_id} with worksheet generation event")
                except Exception as e:
                    logger.error(f"Failed to update session with worksheet info: {e}")
            
            # Create and return response
            worksheet_title = request.title or f"{request.subject} {request.topic} {request.worksheet_type.value.replace('_', ' ').title()} Worksheet"
            response = WorksheetResponse(
                pdf_url=pdf_url,
                worksheet_type=request.worksheet_type,
                subject=request.subject,
                grade=request.grade,
                topic=request.topic,
                title=worksheet_title,
                question_count=request.num_questions,
                session_id=session_id
            )
            
            logger.info(f"Successfully generated {request.worksheet_type} worksheet for {request.subject}, grade {request.grade}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating worksheet: {e}")
            raise Exception(f"Failed to generate worksheet: {str(e)}")
    
    def _retrieve_rag_content(self, 
                             subject: str, 
                             grade: str, 
                             topic: str, 
                             worksheet_type: WorksheetType,
                             num_questions: int,
                             language: str) -> str:
        """Retrieve content from the RAG system based on subject, grade, and topic."""
        try:
            if not self.genai_client:
                logger.error("Google Generative AI client not initialized")
                return "Failed to initialize AI client for content generation."
            
            # Create the prompt for RAG
            type_info = self._worksheet_type_prompts[worksheet_type]
            
            prompt = f"""
You are an expert educational worksheet creator for grade {grade} students.
Create a complete {worksheet_type.value.replace('_', ' ')} worksheet about {topic} for {subject}.

{type_info['instruction'].format(num_questions=num_questions)}
{type_info['format']}

The worksheet must include exactly {num_questions} questions related to {topic} in {subject} appropriate for grade {grade} students.
Make sure all questions are factually correct and aligned with educational standards.

For each question, also provide the correct answer separately in an answer key section.

Language: {language}
            """
            
            # Configure the RAG request
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
            ]
            
            tools = [
                types.Tool(
                    retrieval=types.Retrieval(
                        vertex_rag_store=types.VertexRagStore(
                            rag_resources=[
                                types.VertexRagStoreRagResource(
                                    rag_corpus="projects/purva-api/locations/us-central1/ragCorpora/4611686018427387904"
                                )
                            ],
                            similarity_top_k=20,
                        )
                    )
                )
            ]
            
            # Configure generation parameters
            generate_content_config = types.GenerateContentConfig(
                temperature=0.2,  # Lower temperature for more factual/consistent output
                top_p=0.95,
                max_output_tokens=65535,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    )
                ],
                tools=tools,
            )
            
            # Call the RAG system
            logger.info(f"Calling RAG system for {subject}, grade {grade}, topic {topic}")
            response = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_content_config,
            )
            
            if response and response.candidates and response.candidates[0].content:
                content = response.candidates[0].content.parts[0].text
                logger.info(f"Successfully retrieved content from RAG (length: {len(content)} chars)")
                return content
            else:
                logger.error("Empty response from RAG system")
                return ""
                
        except Exception as e:
            logger.error(f"Error retrieving content from RAG: {e}")
            return ""
    
    def _process_rag_response(self, 
                             rag_content: str, 
                             worksheet_type: WorksheetType,
                             include_answers: bool = True) -> Dict[str, Any]:
        """Process the RAG response into a structured format for PDF generation."""
        try:
            # Split content into questions and answers
            parts = rag_content.split("Answer Key", 1)
            
            questions_section = parts[0].strip()
            answers_section = parts[1].strip() if len(parts) > 1 and include_answers else ""
            
            # Extract title from the beginning if present
            title_lines = questions_section.split('\n', 3)
            title = title_lines[0].strip()
            if len(title_lines) > 1 and not title_lines[1].strip():
                # Use the first line as title if followed by empty line
                questions_section = '\n'.join(title_lines[2:])
            else:
                # Default title will be used instead
                title = ""
            
            # Parse questions based on worksheet type
            questions = []
            
            # Split by numbered lines (1., 2., etc.)
            import re
            question_blocks = re.split(r'\n\s*\d+\.', questions_section)
            if len(question_blocks) > 1:
                # Remove any content before the first question
                question_blocks = question_blocks[1:]
                
                for q in question_blocks:
                    questions.append(q.strip())
            else:
                # Alternative split method if numbered format not found
                questions = [q.strip() for q in questions_section.split('\n\n') if q.strip()]
            
            # Structure content for PDF generation
            return {
                "title": title,
                "questions": questions,
                "answers": answers_section if include_answers else "",
                "worksheet_type": worksheet_type
            }
            
        except Exception as e:
            logger.error(f"Error processing RAG response: {e}")
            return {
                "title": "Error in processing worksheet content",
                "questions": ["Error: Could not process the worksheet content correctly."],
                "answers": "",
                "worksheet_type": worksheet_type
            }
    
    def _generate_pdf(self, 
                     worksheet_content: Dict[str, Any], 
                     request: WorksheetRequest) -> Tuple[str, str]:
        """Generate a PDF worksheet from the processed content."""
        try:
            # Create a unique filename
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            
            # Create filename using subject, topic and timestamp
            subject_slug = request.subject.replace(" ", "_").lower()
            topic_slug = request.topic.replace(" ", "_").lower()
            worksheet_type = request.worksheet_type.value
            
            filename = f"worksheet_{subject_slug}_{topic_slug}_{worksheet_type}_{timestamp}_{unique_id}.pdf"
            filepath = os.path.join(self.pdf_dir, filename)
            
            # Create the PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                alignment=TA_CENTER,
                fontSize=16,
                spaceAfter=12
            )
            
            header_style = ParagraphStyle(
                'Header',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=10
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8
            )
            
            # Create document elements
            elements = []
            
            # Add custom title or use generated title
            title_text = request.title or worksheet_content.get("title") or f"{request.subject} - {request.topic} - {request.worksheet_type.value.replace('_', ' ').title()} Worksheet"
            elements.append(Paragraph(title_text, title_style))
            
            # Add subtitle with grade info
            subtitle = f"Grade {request.grade} - {datetime.now().strftime('%B %d, %Y')}"
            elements.append(Paragraph(subtitle, styles['Italic']))
            elements.append(Spacer(1, 20))
            
            # Add instructions based on worksheet type
            if request.worksheet_type == WorksheetType.MULTIPLE_CHOICE:
                instructions = "Instructions: Circle the letter of the correct answer for each question."
            elif request.worksheet_type == WorksheetType.FILL_IN_BLANKS:
                instructions = "Instructions: Fill in the blanks with the correct word or phrase."
            else:  # SHORT_ANSWERS
                instructions = "Instructions: Answer each question with complete sentences."
            
            elements.append(Paragraph(instructions, normal_style))
            elements.append(Spacer(1, 20))
            
            # Add questions
            elements.append(Paragraph("Questions:", header_style))
            
            for i, question in enumerate(worksheet_content["questions"]):
                # Add question number
                q_text = f"{i+1}. {question}"
                elements.append(Paragraph(q_text, normal_style))
                elements.append(Spacer(1, 10))
            
            # Add answers if included
            if worksheet_content["answers"] and request.include_answers:
                elements.append(Paragraph("Answer Key:", header_style))
                elements.append(Paragraph(worksheet_content["answers"], normal_style))
            
            # Build the PDF
            doc.build(elements)
            
            # Create URL for the file
            base_url = "/generated_pdfs"
            pdf_url = f"{base_url}/{filename}"
            
            logger.info(f"Generated PDF worksheet at {filepath}")
            return filepath, pdf_url
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise Exception(f"Failed to generate PDF: {str(e)}")


# Initialize the service
worksheet_generator_service = WorksheetGeneratorService()
