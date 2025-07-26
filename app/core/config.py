import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
# GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Vertex AI Configuration
VERTEX_AI_PROJECT_ID = os.getenv("VERTEX_AI_PROJECT_ID", FIREBASE_PROJECT_ID)
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
GEMINI_MODEL = "gemini-2.0-flash-001"
