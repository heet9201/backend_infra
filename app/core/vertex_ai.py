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

def generate_image(prompt: str) -> Optional[str]:
    """
    Generate an image based on a prompt using Vertex AI, and save it locally.
    
    Args:
        prompt: The description of the image to generate
        
    Returns:
        Optional[str]: Local file path to the generated image or None if generation failed
    """
    try:
        # Create a directory for storing generated images if it doesn't exist
        import os
        import hashlib
        import requests
        import time
        import uuid
        import random
        import math
        from pathlib import Path
        from PIL import Image, ImageDraw, ImageFont
        from datetime import datetime

        # Create a unique folder for storing generated images
        image_dir = os.path.join(os.getcwd(), "generated_images")
        os.makedirs(image_dir, exist_ok=True)
        
        # Generate a unique filename based on prompt
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        filename = f"visual_aid_{prompt_hash}_{timestamp}_{unique_id}.png"
        local_path = os.path.join(image_dir, filename)
        
        logger.info(f"Image generation requested with prompt: {prompt[:50]}...")
        
        # Check if Vertex AI Imagen API is available for real image generation
        try:
            if VERTEX_AI_AVAILABLE and VERTEX_AI_INITIALIZED:
                # Attempt to use Vertex AI Imagen for image generation if available
                try:
                    from vertexai.preview.vision_models import Image as VImage
                    from vertexai.preview.vision_models import ImageGenerationModel
                    
                    logger.info("Using Vertex AI Imagen for image generation")
                    
                    # Try to use the best model available, starting with the highest quality
                    try:
                        # First try Imagen 4 (highest quality model)
                        logger.info("Attempting to use Imagen 4 model")
                        imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@006")
                        logger.info("Using Imagen 4 model for highest quality generation")
                    except Exception as e1:
                        logger.warning(f"Failed to initialize Imagen 4, trying Imagen 3 Turbo: {e1}")
                        try:
                            # Fall back to Imagen 3 Turbo
                            imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@005")
                            logger.info("Using Imagen 3 Turbo model for high quality generation")
                        except Exception as e2:
                            logger.warning(f"Failed to initialize Imagen 3 Turbo, trying Imagen 3: {e2}")
                            try:
                                # Try to initialize the standard Imagen 3 model
                                imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@003")
                                logger.info("Using Imagen 3 model for high quality generation")
                            except Exception as e3:
                                logger.warning(f"Failed to initialize Imagen 3, falling back to Imagen 2: {e3}")
                                # Fall back to Imagen 2
                                imagen_model = ImageGenerationModel.from_pretrained("imagegeneration@002")
                                logger.info("Using Imagen 2 model")
                    
                    # Create a clean, focused educational prompt
                    enhanced_prompt = f"""
Create a clear, high-quality educational illustration about: {prompt}

Key points:
- This image will be used for teaching students
- Create a detailed and accurate visual representation
- Focus on clarity and educational value
- Include appropriate labels for key elements
- Use professional, textbook-quality style
- Clean layout with good use of space
- No watermarks or text overlays
"""
                    
                    # Generate the image with optimal parameters
                    random_seed = random.randint(100, 10000)
                    
                    # Set base parameters
                    generation_params = {
                        "prompt": enhanced_prompt,
                        "number_of_images": 1,
                    }
                    
                    # Add optimal parameters based on the model version
                    if "imagegeneration@006" in str(imagen_model):
                        # For Imagen 4, use the highest quality settings (no seed due to watermark restrictions)
                        generation_params.update({
                            "language": "en",
                            "mode": "hd",  # Use HD mode for best quality
                            "guidance_scale": 12.0,  # Higher guidance for better prompt following
                            "negative_prompt": "blurry, distorted, text errors, watermarks, signatures, low quality, pixelated, ugly, disfigured, bad proportions"
                        })
                    elif "imagegeneration@005" in str(imagen_model):
                        # For Imagen 3 Turbo, use the highest quality settings
                        # Check if this version supports seed with watermark
                        try:
                            generation_params.update({
                                "language": "en",
                                "mode": "hd",  # Use HD mode for best quality
                                "guidance_scale": 12.0,  # Higher guidance for better prompt following
                                "negative_prompt": "blurry, distorted, text errors, watermarks, signatures, low quality",
                                "seed": random_seed
                            })
                        except Exception:
                            # If seed with watermark fails, try without seed
                            generation_params.update({
                                "language": "en",
                                "mode": "hd",
                                "guidance_scale": 12.0,
                                "negative_prompt": "blurry, distorted, text errors, watermarks, signatures, low quality"
                            })
                    elif "imagegeneration@003" in str(imagen_model) or "imagegeneration@002" in str(imagen_model):
                        # For standard Imagen 3/2
                        generation_params.update({
                            "language": "en",
                            "mode": "standard",  # Balance between quality and speed
                            "negative_prompt": "blurry, distorted, text errors, watermarks, signatures",
                            "seed": random_seed
                        })
                    
                    # Generate the image
                    generated_image = imagen_model.generate_images(**generation_params)
                    
                    # Save the image locally
                    generated_image[0].save(local_path)
                    logger.info(f"Image successfully generated and saved at: {local_path}")
                    
                    # Return the local path
                    return local_path
                except (ImportError, Exception) as ve:
                    logger.error(f"Vertex AI Imagen not available or error: {ve}")
                    # Fall back to generating a simple image
        except Exception as vertex_error:
            logger.error(f"Error with Vertex AI image generation: {vertex_error}")
        
        # Fallback 1: Try to download a subject-specific image from Unsplash
        try:
            # Extract specific keywords from the prompt
            keywords = extract_specific_keywords_from_prompt(prompt)
            
            # Generate a deterministic seed for consistent results
            seed = int(hashlib.md5((prompt + keywords).encode()).hexdigest(), 16) % 10000
            
            # Unsplash URL with educational content search
            unsplash_url = f"https://source.unsplash.com/random/1200x900?{keywords}&educational&sig={seed}"
            
            # Download the image
            response = requests.get(unsplash_url, timeout=15)
            if response.status_code == 200:
                with open(local_path, 'wb') as img_file:
                    img_file.write(response.content)
                logger.info(f"Downloaded image from Unsplash and saved at: {local_path}")
                return local_path
        except Exception as req_error:
            logger.error(f"Error downloading image: {req_error}")
        
        # Fallback 2: Create a simple placeholder image
        try:
            # Create a basic placeholder with the prompt text
            width, height = 1000, 800
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("Arial", 36)
                text_font = ImageFont.truetype("Arial", 18)
            except IOError:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Extract a title from the prompt
            title = extract_title_from_prompt(prompt)
            
            # Draw border and background
            draw.rectangle((50, 50, width-50, height-50), outline=(0, 0, 0), width=2)
            
            # Add title
            draw.text((width/2, 100), title.capitalize(), fill=(0, 0, 100), font=title_font, anchor="mm")
            
            # Add prompt as content
            # Wrap text to fit in the image
            prompt_lines = []
            words = prompt.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) <= 60:  # Limit line length
                    current_line = test_line
                else:
                    prompt_lines.append(current_line)
                    current_line = word
            
            if current_line:
                prompt_lines.append(current_line)
            
            # Draw the wrapped text
            y_position = height/2
            for line in prompt_lines:
                draw.text((width/2, y_position), line, fill=(0, 0, 0), font=text_font, anchor="mm")
                y_position += 30
            
            # Add a message indicating this is a placeholder
            draw.text((width/2, height-50), "This is a placeholder for the requested educational visual", 
                     fill=(100, 100, 100), font=text_font, anchor="mm")
            
            # Save the image
            image.save(local_path)
            logger.info(f"Generated placeholder image with text and saved at: {local_path}")
            return local_path
            
        except Exception as pil_error:
            logger.error(f"Error generating placeholder image: {pil_error}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

def extract_title_from_prompt(prompt: str) -> str:
    """Extract a title from the prompt"""
    # Simple heuristic to get a title - use first sentence or first few words
    first_part = prompt.split('.')[0].strip()
    
    # If too long, take just the first 6-8 words
    words = first_part.split()
    
    # Extract the most meaningful words
    # Look for patterns like "Draw/Create/Make [a/an] [X]" and extract X
    title_patterns = [
        r'(?:draw|create|make|generate|show)\s+(?:a|an|the)?\s+([a-zA-Z\s]+)',
        r'(?:diagram|image|picture|illustration) of\s+([a-zA-Z\s]+)',
        r'showing\s+(?:the)?\s+([a-zA-Z\s]+)',
        r'illustrating\s+(?:the)?\s+([a-zA-Z\s]+)'
    ]
    
    import re
    for pattern in title_patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            extracted = match.group(1).strip()
            # Take first 5-7 words of extracted portion
            title_words = extracted.split()
            if len(title_words) > 7:
                return " ".join(title_words[:7]).capitalize()
            return extracted.capitalize()
    
    # If no pattern match, just take first 6 words
    if len(words) > 6:
        return " ".join(words[:6]).capitalize()
    return first_part.capitalize()

def extract_specific_keywords_from_prompt(prompt: str) -> str:
    """Extract specific, content-focused keywords from the prompt for better image matching"""
    # Look for specific educational terms and subjects
    import re
    
    # Try to extract the main topic
    topic_patterns = [
        r'(?:about|showing|illustrating|depicting)\s+([a-zA-Z\s]+)',
        r'(?:of|for)\s+([a-zA-Z\s]+)',
        r'([a-zA-Z\s]+)(?:\s+diagram|chart|illustration)'
    ]
    
    for pattern in topic_patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            topic = match.group(1).strip()
            # Limit to first 3-4 words for better search results
            topic_words = topic.split()
            if len(topic_words) > 4:
                topic = " ".join(topic_words[:4])
            return topic
    
    # If no pattern match, use first few words of prompt
    words = prompt.lower().split()
    filtered_words = [w for w in words if len(w) > 3 and w not in ['show', 'create', 'make', 'draw', 'about', 'with', 'using']]
    
    if filtered_words:
        # Take the first 2-3 substantive words
        return " ".join(filtered_words[:3])
    
    # Fallback - just use the first few words
    return " ".join(words[:3])