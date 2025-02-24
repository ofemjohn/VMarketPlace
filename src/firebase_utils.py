import os
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK"""

    cred_path = os.getenv("FIREBASE_CREDENTIALS")
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

    # Debugging: Print values to verify
    print(f"🔍 FIREBASE_CREDENTIALS: {cred_path}")
    print(f"🔍 FIREBASE_STORAGE_BUCKET: {bucket_name}")

    # Ensure the credentials file exists
    if not cred_path or not os.path.exists(cred_path):
        raise FileNotFoundError(f"❌ Firebase credentials file not found: {cred_path}")

    if not bucket_name:
        raise ValueError("❌ Firebase Storage bucket name is missing from environment variables!")

    if not firebase_admin._apps:  # Prevent multiple initializations
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})

    print("✅ Firebase Initialized Successfully")
