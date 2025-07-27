import os
import uuid
import time
import base64
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime
from pathlib import Path
import tempfile

# PDF processing
import fitz  # PyMuPDF
from PIL import Image
import io

# AI and content generation
from app.core.vertex_ai import generate_content
from app.models.content_generation_model import (
    ContentType, OutputFormat, ResearchDepth, ContentLength, 
    ContentGenerationRequest, ContentGenerationResponse
)
from app.utils.logger import logger
from app.utils.language_utils import translate_text, detect_language


class ContentGenerationService:
    """Service for generating educational content from images and PDFs."""
    
    def __init__(self):
        # Create directories for storing uploaded files
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Map content generation parameters to prompt modifiers
        self._content_type_prompts = {
            ContentType.DETAILED_CONTENT: "Create detailed, comprehensive educational content about",
            ContentType.SUMMARY: "Provide a concise summary of the key information in",
            ContentType.KEY_POINTS: "Extract and list the key points from",
            ContentType.STUDY_GUIDE: "Create a structured study guide based on",
            ContentType.PRACTICE_QUESTIONS: "Generate practice questions with answers based on"
        }
        
        self._output_format_prompts = {
            OutputFormat.TEXT: "in flowing paragraphs of text",
            OutputFormat.BULLET_POINTS: "in a bulleted list format with clear categories",
            OutputFormat.QA_FORMAT: "in a question-and-answer format",
            OutputFormat.MIND_MAP: "in a textual mind map format with main topics and branches",
            OutputFormat.FLASHCARDS: "as flashcard pairs with questions/prompts and answers"
        }
        
        self._research_depth_prompts = {
            ResearchDepth.SURFACE: "focusing only on the most apparent information",
            ResearchDepth.BASIC: "with basic analysis of the main concepts",
            ResearchDepth.MODERATE: "with moderate depth analysis and connections between concepts",
            ResearchDepth.DETAILED: "with detailed analysis, examples, and contextual information",
            ResearchDepth.DEEP: "with deep analysis, historical context, and theoretical foundations"
        }
        
        self._content_length_prompts = {
            ContentLength.CONCISE: "Keep it very concise (100-200 words).",
            ContentLength.BRIEF: "Keep it brief (200-400 words).",
            ContentLength.MODERATE: "Provide moderate detail (400-800 words).",
            ContentLength.DETAILED: "Make it detailed (800-1500 words).",
            ContentLength.COMPREHENSIVE: "Make it comprehensive (1500-2500 words)."
        }

    async def process_image(self, image_data: bytes, settings: ContentGenerationRequest, user_id: Optional[str] = None, session_id: Optional[str] = None) -> ContentGenerationResponse:
        """Process an uploaded image and generate educational content based on it."""
        try:
            # Save image to a temporary file
            image_path = self._save_temp_file(image_data, "image")
            
            # Extract text content from the image
            image_content = self._extract_text_from_image(image_path)
            
            # Generate educational content from the image
            return await self._generate_content(image_content, "image", settings, user_id, session_id)
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise Exception(f"Failed to process image: {str(e)}")

    async def process_pdf(self, pdf_data: bytes, settings: ContentGenerationRequest, user_id: Optional[str] = None, session_id: Optional[str] = None) -> ContentGenerationResponse:
        """Process an uploaded PDF and generate educational content based on it."""
        try:
            # Save PDF to a temporary file
            pdf_path = self._save_temp_file(pdf_data, "pdf")
            
            # Extract text content from the PDF
            pdf_content = self._extract_text_from_pdf(pdf_path)
            
            # Generate educational content from the PDF
            return await self._generate_content(pdf_content, "pdf", settings, user_id, session_id)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def _save_temp_file(self, file_data: bytes, file_type: str) -> str:
        """Save uploaded file data to a temporary file and return the file path."""
        try:
            # Create a unique filename
            filename_hash = hashlib.md5(file_data).hexdigest()[:10]
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            
            file_extension = "pdf" if file_type == "pdf" else "png"
            filename = f"upload_{filename_hash}_{timestamp}_{unique_id}.{file_extension}"
            filepath = os.path.join(self.upload_dir, filename)
            
            # Save the file
            with open(filepath, "wb") as f:
                f.write(file_data)
                
            logger.info(f"Saved uploaded {file_type} as {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving {file_type}: {e}")
            raise Exception(f"Failed to save {file_type}: {str(e)}")
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text content from an image using OCR."""
        try:
            # Import Google Cloud Vision API for OCR
            from google.cloud import vision
            
            # Initialize Vision client
            client = vision.ImageAnnotatorClient()
            
            # Read image file
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            
            # Create image object
            image = vision.Image(content=content)
            
            # Detect text
            response = client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                logger.warning(f"No text found in image {image_path}")
                return "No text content detected in the image."
            
            # Extract full text from first annotation (contains all text)
            extracted_text = texts[0].description
            
            # Also extract any labels/objects in the image
            object_response = client.label_detection(image=image)
            labels = object_response.label_annotations
            
            label_text = ""
            if labels:
                label_list = [f"{label.description} ({int(label.score * 100)}%)" for label in labels[:10]]
                label_text = "Image contains: " + ", ".join(label_list)
            
            # Combine extracted text and labels
            complete_content = f"{extracted_text}\n\n{label_text}" if label_text else extracted_text
            
            logger.info(f"Successfully extracted text from image {image_path}")
            return complete_content
            
        except ImportError:
            logger.warning("Google Cloud Vision not available, using placeholder text")
            return "Image text extraction service unavailable. Please ensure Google Cloud Vision API is configured."
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return f"Error extracting text from image: {str(e)}"
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF."""
        try:
            # Open the PDF
            pdf_document = fitz.open(pdf_path)
            
            # Extract text from each page
            text_content = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text_content.append(page.get_text())
            
            # Combine all pages
            complete_content = "\n\n".join(text_content)
            
            logger.info(f"Successfully extracted text from PDF {pdf_path} ({len(pdf_document)} pages)")
            return complete_content
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return f"Error extracting text from PDF: {str(e)}"
    
    async def _generate_content(self, 
                                source_content: str, 
                                source_type: str,
                                settings: ContentGenerationRequest,
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None) -> ContentGenerationResponse:
        """Generate content based on extracted text and requested output format."""
        try:
            # Determine which prompt to use based on output_format
            if settings.output_format == OutputFormat.BULLET_POINTS:
                # Generate bullet point summary
                prompt = f"""
You are an expert educational content creator. Your task is to analyze the following content extracted from a {source_type}
and create a comprehensive summary with bullet points.

Focus on the main concepts, important details, and key takeaways from the content.
Create 5-10 well-organized bullet points that highlight the most important information.

Your response should start with the introduction: "Here is a summary of the content:" and then continue with bullet points.

Format your response like this:

Here is a summary of the content:

• [Main point 1]
• [Main point 2]
  • [Sub-point 2.1]
  • [Sub-point 2.2]
• [Main point 3]

Use clear and concise language appropriate for educational purposes.

SOURCE CONTENT:
{source_content[:3000]}  # Limit source content to prevent token overflow
"""
            else:  # Default to QA_FORMAT
                # Generate Q&A content
                prompt = f"""
You are an expert educational content creator. Your task is to analyze the following content extracted from a {source_type}
and create a set of study questions with detailed answers.

Create 3-5 high-quality questions that test understanding of the key concepts in the content.
Each question should have a comprehensive answer that provides valuable educational content.

Your response should start with the introduction: "Here is a Q&A based on the content:" and then continue with the questions and answers.

Format your response in a clean Question and Answer format like this:

Here is a Q&A based on the content:

Q1: [Question text]
A1: [Answer text]

Q2: [Question text] 
A2: [Answer text]

Keep your questions focused on the most important aspects of the content.

SOURCE CONTENT:
{source_content[:3000]}  # Limit source content to prevent token overflow
"""
            
            # Generate content using Vertex AI
            generated_content = generate_content(prompt, temperature=0.2)
            
            # If language is not English and different from requested language, translate
            if settings.local_language.lower() != "english":
                generated_content = translate_text(generated_content, settings.local_language)
            
            # Create response object with parameters
            response = ContentGenerationResponse(
                content=generated_content,
                language=settings.local_language,
                content_type=ContentType.STUDY_GUIDE,
                output_format=settings.output_format,  # Use the requested output format
                source_type=source_type,
                additional_resources=None,
                session_id=session_id,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise Exception(f"Failed to generate content: {str(e)}")

content_generation_service = ContentGenerationService()
