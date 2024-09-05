# src/firebase_utils.py
import os
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase Initialization
firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS')
cred = credentials.Certificate(firebase_creds_path)

# Initialize the Firebase app if it hasn't been initialized already
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
    })
