import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import GOOGLE_CREDENTIALS

cred = credentials.Certificate(GOOGLE_CREDENTIALS)
firebase_admin.initialize_app(cred)

db = firestore.client()
