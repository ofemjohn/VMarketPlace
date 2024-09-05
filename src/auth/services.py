import os
import re
from fastapi import Depends, HTTPException, status, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime
from typing import Optional, List
from firebase_admin import auth, storage
from src.firebase_utils import *



from src.auth.models import User, UserRole
from src.auth.schemas import UserCreate, UserUpdate
from src.database import get_db

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Password hashing context setup
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080
REFRESH_TOKEN_EXPIRE_DAYS = 30

# OAuth2 scheme for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}

# Utility function to create access token
async def create_access_token(email: str, id: int) -> str:
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Utility function to create refresh token
async def create_refresh_token(email: str, id: int) -> str:
    encode = {"sub": email, "id": id}
    expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Token Management
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

# Authenticate and retrieve the current user based on the JWT token
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# User Registration & Authentication
async def create_user(db: Session, user: UserCreate, role: UserRole = UserRole.user, is_super_admin: bool = False) -> User:
    if await existing_user_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    if user.username and await existing_user_by_username(db, user.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already in use")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address")
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=bcrypt_context.hash(user.password) if user.password else None,
        latitude=user.latitude,
        longitude=user.longitude,
        role=role,
        is_super_admin=is_super_admin,
        expo_push_token=user.expo_push_token  
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def authenticate(db: Session, identifier: str, password: str) -> Optional[User]:
    db_user = db.query(User).filter((User.username == identifier) | (User.email == identifier)).first()
    if db_user and bcrypt_context.verify(password, db_user.hashed_password):
        return db_user
    return None

# Firebase Social Login (Google) Example
async def google_auth(token: str, db: Session = Depends(get_db)) -> User:
    try:
        decoded_token = auth.verify_id_token(token)
        email = decoded_token['email']
        user = await existing_user_by_email(db, email)
        if not user:
            user = User(
                email=email,
                username=email.split('@')[0],
                googleId=decoded_token['uid'],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to authenticate with Google")
    
    
async def facebook_auth(token: str, db: Session = Depends(get_db)) -> User:
    try:
        decoded_token = auth.verify_id_token(token)  # You may need to decode the Facebook token differently
        email = decoded_token['email']
        user = await existing_user_by_email(db, email)
        if not user:
            user = User(
                email=email,
                username=email.split('@')[0],
                facebook_id=decoded_token['id'],  # Store Facebook ID
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to authenticate with Facebook")
    

# Profile Management
async def update_user(db: Session, db_user: User, user_update: UserUpdate):
    if user_update.profile_picture_url is not None:
        db_user.profile_picture_url = str(user_update.profile_picture_url)  # Convert HttpUrl to string
    if user_update.latitude is not None:
        db_user.latitude = user_update.latitude
    if user_update.longitude is not None:
        db_user.longitude = user_update.longitude
    if user_update.email is not None:
        db_user.email = user_update.email
    db.commit()
    db.refresh(db_user)


async def update_user_location(db: Session, user: User, latitude: float, longitude: float) -> User:
    user.latitude = latitude
    user.longitude = longitude
    db.commit()
    db.refresh(user)
    return user


# Upload a profile picture to Firebase Storage and return its public URL
async def upload_profile_picture(user: User, file: UploadFile) -> str:
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format. Only .jpg and .png are allowed.")
    
    bucket = storage.bucket()

    # Delete the old profile picture if it exists
    if user.profile_picture_url:
        # Extract the blob name from the URL and delete it
        blob_name = user.profile_picture_url.split("/")[-1]
        old_blob = bucket.blob(f"profile_pictures/{blob_name}")
        if old_blob.exists():
            old_blob.delete()

    # Generate a unique filename using user ID and current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # Corrected this line
    extension = file.filename.split('.')[-1]
    unique_filename = f"{user.id}_{timestamp}.{extension}"

    # Create a new blob for the new profile picture
    blob = bucket.blob(f"profile_pictures/{unique_filename}")

    try:
        # Upload the new file
        blob.upload_from_file(file.file)
        # Make the blob publicly accessible
        blob.make_public()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image. Please try again later.")

    # Return the public URL of the uploaded file
    return blob.public_url


# User Query Functions
async def existing_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

async def existing_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

async def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

async def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()


