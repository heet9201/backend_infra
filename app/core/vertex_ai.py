import os
from app.core.config import VERTEX_AI_PROJECT_ID, VERTEX_AI_LOCATION, GEMINI_MODEL
from app.utils.logger import logger
from typing import List, Optional
import tempfile

# Try to import Vertex AI, handle gracefully if not available
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    from vertexai.generative_models import SafetySetting, HarmCategory, HarmBlockThreshold
    VERTEX_AI_AVAILABLE = True
    logger.info("Vertex AI imports successful")
    
    # Initialize Vertex AI with proper authentication
    try:
        # Use the same credentials as Firebase
        from google.cloud import storage
        
        # Download credentials if not already available
        FIREBASE_CREDENTIALS_PATH = os.path.join(tempfile.gettempdir(), "firebase.json")
        
        def setup_vertex_ai_credentials():
            """Setup credentials for Vertex AI using the same as Firebase"""
            try:
                if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
                    # Download Firebase credentials to temp file
                    CLOUD_STORAGE_BUCKET = "purva-api_cloudbuild"
                    CLOUD_STORAGE_BLOB_NAME = "source/purva-api-74d1474dc39b.json"
                    
                    storage_client = storage.Client()
                    bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
                    blob = bucket.blob(CLOUD_STORAGE_BLOB_NAME)
                    blob.download_to_filename(FIREBASE_CREDENTIALS_PATH)
                    logger.info("Downloaded credentials for Vertex AI")
                
                # Set environment variable for Google Application Credentials
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = FIREBASE_CREDENTIALS_PATH
                
                # Initialize Vertex AI
                vertexai.init(
                    project=VERTEX_AI_PROJECT_ID, 
                    location=VERTEX_AI_LOCATION,
                    credentials=None  # Will use the credentials from environment variable
                )
                logger.info(f"Vertex AI initialized with project: {VERTEX_AI_PROJECT_ID}, location: {VERTEX_AI_LOCATION}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to setup Vertex AI credentials: {e}")
                return False
        
        # Try to setup credentials and initialize
        VERTEX_AI_INITIALIZED = setup_vertex_ai_credentials()
        
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI: {e}")
        VERTEX_AI_INITIALIZED = False
        
except ImportError as e:
    logger.warning(f"Vertex AI not available: {e}")
    VERTEX_AI_AVAILABLE = False
    VERTEX_AI_INITIALIZED = False
    
    # Mock classes for when Vertex AI is not available
    class SafetySetting:
        def __init__(self, category, threshold):
            pass
    
    class HarmCategory:
        HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
        HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
    
    class HarmBlockThreshold:
        BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"
        BLOCK_HIGH_ONLY = "BLOCK_HIGH_ONLY"
    
    class GenerativeModel:
        def __init__(self, model_name, safety_settings=None):
            pass
        
        def generate_content(self, prompt, generation_config=None):
            class MockResponse:
                text = "This is a mock response. Vertex AI is not available in this environment."
            return MockResponse()
    
    # Mock classes for when Vertex AI is not available
    class SafetySetting:
        def __init__(self, category, threshold):
            pass
    
    class HarmCategory:
        HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
        HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
    
    class HarmBlockThreshold:
        BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"
        BLOCK_HIGH_ONLY = "BLOCK_HIGH_ONLY"
    
    class GenerativeModel:
        def __init__(self, model_name, safety_settings=None):
            pass
        
        def generate_content(self, prompt, generation_config=None):
            class MockResponse:
                text = "This is a mock response. Vertex AI is not available in this environment."
            return MockResponse()

def get_safety_settings() -> List[SafetySetting]:
    """Get safety settings for educational content"""
    if not VERTEX_AI_AVAILABLE or not VERTEX_AI_INITIALIZED:
        return []
    
    return [
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=HarmBlockThreshold.BLOCK_HIGH_ONLY,
        ),
        SafetySetting(
            category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ]

def get_gemini_model() -> GenerativeModel:
    """Get the configured Gemini model with safety settings"""
    try:
        if not VERTEX_AI_AVAILABLE or not VERTEX_AI_INITIALIZED:
            logger.warning("Vertex AI not properly initialized, returning mock model")
            return GenerativeModel(GEMINI_MODEL)
            
        return GenerativeModel(
            model_name=GEMINI_MODEL,
            safety_settings=get_safety_settings()
        )
    except Exception as e:
        logger.error(f"Error initializing Gemini model: {e}")
        return GenerativeModel(GEMINI_MODEL)

def generate_content(prompt: str, temperature: float = 0.7) -> str:
    """Generate content using Vertex AI Gemini model"""
    try:
        if not VERTEX_AI_AVAILABLE or not VERTEX_AI_INITIALIZED:
            logger.warning("Vertex AI not available, this should not happen in production")
            return "Vertex AI is not properly configured. Please check your Google Cloud credentials and project settings."
        
        model = get_gemini_model()
        
        generation_config = {
            "temperature": temperature,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return f"I apologize, but I couldn't generate content at this time. Error: {str(e)}"

def generate_educational_content(prompt: str, language: str = "English") -> str:
    """Generate educational content with specific settings for teaching"""
    try:
        if not VERTEX_AI_AVAILABLE or not VERTEX_AI_INITIALIZED:
            logger.error("Vertex AI not properly configured for educational content generation")
            return """I apologize, but the AI content generation service is currently unavailable. 

This appears to be a configuration issue with Google Cloud Vertex AI. To resolve this:

1. Ensure Google Cloud credentials are properly configured
2. Verify the project has Vertex AI API enabled
3. Check that the service account has the necessary permissions

For immediate assistance, please contact your system administrator or refer to the Google Cloud Vertex AI documentation."""
        
        educational_prompt = f"""You are an AI teaching assistant called "Sahayak" designed to help teachers in multi-grade, low-resource classrooms in India. 

Language: {language}
Cultural Context: Indian educational system, rural and semi-urban contexts

Guidelines:
- Keep content simple, engaging, and age-appropriate
- Use local cultural references and examples
- Make content suitable for multi-grade teaching
- Focus on practical, hands-on learning approaches
- Use simple vocabulary that teachers can easily explain

Request: {prompt}

Please provide helpful educational content following these guidelines:"""

        return generate_content(educational_prompt, temperature=0.6)
    except Exception as e:
        logger.error(f"Error generating educational content: {e}")
        return f"I'm here to help create educational content, but I'm experiencing technical difficulties. Error: {str(e)}"
