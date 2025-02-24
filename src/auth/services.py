import os
import re
from fastapi import Depends, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime
from typing import Optional, List
from firebase_admin import storage
from src.firebase_utils import initialize_firebase
from src.auth.models import User, UserRole
from src.auth.schemas import UserCreate, UserUpdate
from src.database import get_db
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import google.auth.transport.requests
import google.oauth2.id_token

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Firebase
initialize_firebase()

# Password hashing
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080
REFRESH_TOKEN_EXPIRE_DAYS = 30

# google configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",  # Correct field
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",  # Correct field
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS") == "True",
    VALIDATE_CERTS=os.getenv("VALIDATE_CERTS") == "True",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}

# Utility function to create an access token
async def create_access_token(email: str, id: int) -> str:
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Utility function to create a refresh token
async def create_refresh_token(email: str, id: int) -> str:
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# Authenticate User
async def authenticate(db: Session, identifier: str, password: str) -> Optional[User]:
    db_user = db.query(User).filter((User.full_name == identifier) | (User.email == identifier)).first()
    if db_user and bcrypt_context.verify(password, db_user.hashed_password):
        return db_user
    return None


# Token Validation and Authentication
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        logging.info(f"Received token: {token}")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logging.error("Token payload is missing email")
            raise credentials_exception

        logging.info(f"Extracted email: {email}")
    except JWTError:
        logging.error("JWTError: Invalid token")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logging.error(f"No user found for email: {email}")
        raise credentials_exception

    return user

# Refresh access token
async def refresh_access_token(refresh_token: str) -> str:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        id: int = payload.get("id")
        if email is None or id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return await create_access_token(email, id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# User Registration
async def create_user(db: Session, user: UserCreate, role: UserRole = UserRole.user, is_super_admin: bool = False) -> User:
    if await existing_user_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    if user.full_name and await existing_user_by_username(db, user.full_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address")
    
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=bcrypt_context.hash(user.password) if user.password else None,
        latitude=user.latitude,
        longitude=user.longitude,
        role=role,
        is_super_admin=is_super_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Update User Profile
async def update_user(db: Session, db_user: User, user_update: UserUpdate):
    if user_update.profile_picture_url is not None:
        db_user.profile_picture_url = str(user_update.profile_picture_url)
    if user_update.latitude is not None:
        db_user.latitude = user_update.latitude
    if user_update.longitude is not None:
        db_user.longitude = user_update.longitude
    if user_update.email is not None:
        db_user.email = user_update.email
    if user_update.web_push_subscription is not None:
        db_user.web_push_subscription = user_update.web_push_subscription
    db.commit()
    db.refresh(db_user)


# Upload Profile Picture to Firebase Storage
async def upload_profile_picture(db: Session, user: User, file: UploadFile) -> str:
    """Upload user profile picture to Firebase Storage and return the public URL."""

    # Check if file type is valid
    if file.content_type not in {"image/jpeg", "image/png", "image/jpg"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Only .jpg and .png are allowed.")

    # Get Firebase Storage bucket
    bucket = storage.bucket()
    
    # Remove old profile picture if exists
    if user.profile_picture_url:
        try:
            blob_name = user.profile_picture_url.split("/")[-1]
            old_blob = bucket.blob(f"profile_pictures/{blob_name}")
            if old_blob.exists():
                old_blob.delete()
                print(f"Deleted old profile picture: {blob_name}")
        except Exception as e:
            print(f"Error deleting old profile picture: {e}")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    extension = file.filename.split('.')[-1]
    unique_filename = f"{user.id}_{timestamp}.{extension}"
    blob = bucket.blob(f"profile_pictures/{unique_filename}")

    # Upload file
    try:
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make image publicly accessible
        print(f"Successfully uploaded profile picture: {blob.public_url}")

    except Exception as e:
        print(f"Error uploading file to Firebase: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image.")

    # Save URL to database
    user.profile_picture_url = blob.public_url
    db.commit()
    db.refresh(user)

    return blob.public_url

# Check for existing user by username
async def existing_user_by_username(db: Session, full_name: str) -> Optional[User]:
    return db.query(User).filter(User.full_name == full_name ).first()

# Check for existing user by email
async def existing_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

# Retrieve all users
async def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()


async def generate_reset_token(db: Session, email: str) -> str:
    """Generate and store a password reset token for the user."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None  # User not found

    # Generate token with a 1-hour expiration
    expiration_time = datetime.utcnow() + timedelta(hours=1)
    reset_token = jwt.encode(
        {"email": email, "exp": expiration_time.timestamp()},  # Convert expiration to timestamp
        SECRET_KEY,
        algorithm="HS256"
    )

    # Store the latest token in the database
    user.reset_token = reset_token
    db.commit()
    db.refresh(user)

    return reset_token




async def send_reset_email(email: str, reset_token: str):
    """Send password reset email with a secure link."""
    reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:8000')}/reset-password?token={reset_token}"

    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click <a href='{reset_link}'>here</a> to reset your password.",
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def reset_user_password(db: Session, token: str, new_password: str) -> bool:
    """Validate reset token and update the user's password."""
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        expiration = payload.get("exp")

        # Check if the token is expired
        if datetime.utcnow() > datetime.fromtimestamp(expiration):
            return False  # Token expired

        # Query user by email (not token)
        user = db.query(User).filter(User.email == email).first()
        if not user or user.reset_token != token:
            return False  # User not found or token mismatch

        # Hash the new password
        user.hashed_password = bcrypt_context.hash(new_password)
        user.reset_token = None  # Remove token after successful reset
        db.commit()
        db.refresh(user)

        return True
    except jwt.ExpiredSignatureError:
        return False  # Token expired
    except jwt.InvalidTokenError:
        return False  # Invalid token


import logging

async def verify_google_token(token: str):
    try:
        request = google.auth.transport.requests.Request()
        payload = google.oauth2.id_token.verify_oauth2_token(
            token, request, GOOGLE_CLIENT_ID
        )

        if not payload:
            raise HTTPException(status_code=400, detail="Invalid Google token")
        
        logging.info(f"Decoded Google Token: {payload}")  # ✅ Add Debug Log

        return {
            "email": payload["email"],
            "name": payload.get("name", ""),
            "picture": payload.get("picture", ""),
            "sub": payload.get("sub", ""),
        }
    except ValueError as e:
        logging.error(f"Google Token Verification Failed: {e}")  # ✅ Log Errors
        raise HTTPException(status_code=400, detail="Invalid Google token")


    

async def google_auth(db: Session, token: str):
    """
    Authenticate user with Google OAuth2.
    If user exists, return tokens.
    If user does not exist, create a new user.
    """
    user_info = await verify_google_token(token)
    email = user_info["email"]

    # Check if user already exists
    user = db.query(User).filter((User.email == email) | (User.google_id == user_info["sub"])).first()
    
    if not user:
        # Create a new user
        new_user = User(
            email=email,
            username=email.split("@")[0],  # Generate username from email
            profile_picture_url=user_info.get("picture"),
            google_id=user_info["sub"],  # Store Google ID
            role=UserRole.user
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    else:
        # Update existing user with Google ID if missing
        if not user.google_id:
            user.google_id = user_info["sub"]
            db.commit()
            db.refresh(user)

    # Generate JWT tokens
    access_token = await create_access_token(user.email, user.id)
    refresh_token = await create_refresh_token(user.email, user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_picture_url": user.profile_picture_url,
            "role": user.role.value,
            "created_dt": user.created_dt,
        }
    }
