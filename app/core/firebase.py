import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
import tempfile
import os

# Get a valid temporary path
FIREBASE_CREDENTIALS_PATH = os.path.join(tempfile.gettempdir(), "firebase.json")

# GCS bucket info
CLOUD_STORAGE_BUCKET = "purva-api_cloudbuild"
CLOUD_STORAGE_BLOB_NAME = "source/purva-api-74d1474dc39b.json"

def download_firebase_credentials():
    print(f"Downloading Firebase credentials to {FIREBASE_CREDENTIALS_PATH}")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(CLOUD_STORAGE_BLOB_NAME)
        blob.download_to_filename(FIREBASE_CREDENTIALS_PATH)
        print("Firebase credentials downloaded successfully!")
    except Exception as e:
        print(f"Failed to download Firebase credentials: {e}")
        raise

def initialize_firebase():
    download_firebase_credentials()

    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)

    return firestore.client()
