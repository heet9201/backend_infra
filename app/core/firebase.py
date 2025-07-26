import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage
from google.oauth2 import service_account
import os

# Where to save the downloaded credentials
FIREBASE_CREDENTIALS_PATH = "/tmp/firebase.json"

# Your GCS bucket and blob location
CLOUD_STORAGE_BUCKET = "purva-api_cloudbuild"
CLOUD_STORAGE_BLOB_NAME = "source/purva-api-74d1474dc39b.json"

def download_firebase_credentials():
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        print(f"Downloading Firebase credentials to {FIREBASE_CREDENTIALS_PATH}")

        # Optionally: Load service account manually from bundled file in container/local
        # Otherwise use default credentials (in GCP)
        try:
            storage_client = storage.Client()
        except Exception as e:
            print("Could not initialize default credentials:", e)
            raise

        bucket = storage_client.bucket(CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(CLOUD_STORAGE_BLOB_NAME)
        blob.download_to_filename(FIREBASE_CREDENTIALS_PATH)

        print("Firebase credentials downloaded successfully!")

def initialize_firebase():
    download_firebase_credentials()

    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)

    return firestore.client()
