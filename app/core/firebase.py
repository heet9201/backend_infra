import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import os
from app.core.config import GOOGLE_CREDENTIALS

# Define the Cloud Storage location of the Firebase credentials
CLOUD_STORAGE_BUCKET = "purva-api_cloudbuild"
CLOUD_STORAGE_BLOB_NAME = "source/purva-api-74d1474dc39b.json"

# Initialize Firebase
def initialize_firebase():
    # Check if credentials exist in /tmp, otherwise download from Cloud Storage
    if not os.path.exists(GOOGLE_CREDENTIALS):
        print(f"Downloading Firebase credentials from Cloud Storage to {GOOGLE_CREDENTIALS}")
        
        # Initialize the Cloud Storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(CLOUD_STORAGE_BLOB_NAME)
        
        # Download the Firebase credentials to the local filesystem
        blob.download_to_filename(GOOGLE_CREDENTIALS)
        print("Firebase credentials downloaded successfully!")

    # Initialize Firebase with the credentials
    cred = credentials.Certificate(GOOGLE_CREDENTIALS)
    firebase_admin.initialize_app(cred)

    # Initialize Firestore (db) client
    db = firestore.client()
    
    # Return the db so it can be used elsewhere in your project
    return db
