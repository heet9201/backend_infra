from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user
from app.routes import health
from app.routes import agent
from app.routes import session
from app.routes import content
from app.routes import content_analysis
import os

# Ensure all service singletons are initialized
from app.services.main_agent_service import main_agent_service
from app.services.hyper_local_content_service import hyper_local_content_service
from app.services.visual_aids_service import visual_aids_service
from app.services.content_generation_service import content_generation_service
from app.utils.logger import logger

logger.info("All agent services initialized in main.py")

app = FastAPI(
    title="Sahayak - AI Teaching Assistant API",
    description="""
    Sahayak is an AI Teaching Assistant API designed for multi-grade, low-resource classrooms in India.
    
    ## Features
    
    * **AI Teaching Assistant**: Generate educational content in multiple Indian languages
    * **Visual Aids**: Create educational images for teaching concepts
    * **Hyper-local Content**: Generate culturally relevant educational material
    * **Content Analysis**: Upload images or PDFs for automatic content generation
    * **User Session Management**: Track and continue teaching sessions
    * **Multimedia Support**: Process various media formats for content generation
    * **Customizable Outputs**: Multiple format options for generated content
    * **Multilingual Capabilities**: Support for major Indian languages
    
    This API provides a comprehensive suite of tools to assist teachers in creating,
    customizing, and delivering educational content suited to diverse classroom needs.
    """,
    version="1.2.0"
)

# Create required directories for image storage
generated_images_dir = os.path.join(os.getcwd(), "generated_images")
uploads_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(generated_images_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router, prefix="/user")
app.include_router(health.router, prefix="/health")
app.include_router(agent.router, prefix="/agent", tags=["AI Teaching Assistant"])
app.include_router(session.router, prefix="/session", tags=["User Sessions"])
app.include_router(content.router, tags=["Content Generation"])
app.include_router(content_analysis.router, tags=["Content Analysis"])
app.include_router(content_analysis.content_router, tags=["Simplified Content Generation"])

# Mount the generated_images and uploads directories as static file directories
app.mount("/generated_images", StaticFiles(directory="generated_images"), name="generated_images")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create a static directory for other static assets if it doesn't exist
static_dir = os.path.join(os.getcwd(), "static", "images")
os.makedirs(static_dir, exist_ok=True)

# Create a simple placeholder image if it doesn't exist
placeholder_path = os.path.join(static_dir, "placeholder.png")
if not os.path.exists(placeholder_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new('RGB', (800, 600), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("Arial", 20)
        except IOError:
            font = ImageFont.load_default()
        draw.text((400, 300), "Image Generation Failed", fill=(0, 0, 0), anchor="mm")
        image.save(placeholder_path)
        logger.info(f"Created placeholder image at {placeholder_path}")
    except Exception as e:
        logger.error(f"Failed to create placeholder image: {e}")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# No need for uvicorn.run() in production, App Engine handles this.
