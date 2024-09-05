from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)
    username: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    expo_push_token: Optional[str] = None

# Schema for updating an existing user
class UserUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_picture_url: Optional[HttpUrl]= None
    email: Optional[EmailStr]
    expo_push_token: Optional[str] = None 

# Schema for user login
class UserLogin(BaseModel):
    identifier: str  # This can be either the username or email
    password: str

# Schema for Google login
class UserLoginGoogle(BaseModel):
    google_id: str = None

class UserLoginFacebook(BaseModel):
    facebook_id: str = None


# Schema to represent a user object in response
class UserSchema(BaseModel):
    id: int
    username: Optional[str] = None
    email: EmailStr
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_picture_url: Optional[str] = None
    role: Optional[str] = None
    is_super_admin: Optional[bool] = None
    google_id: Optional[str] = None
    facebook_id: Optional[str] = None
    created_dt: datetime

    class Config:
        from_attributes = True
