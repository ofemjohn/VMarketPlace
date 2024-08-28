from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)
    username: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float]
    longitude: Optional[float]

# Schema for updating an existing user
class UserUpdate(BaseModel):
    latitude: Optional[float]
    longitude: Optional[float]
    profile_picture_url: Optional[HttpUrl]
    email: Optional[EmailStr]

# Schema for user login
class UserLogin(BaseModel):
    identifier: str  # This can be either the username or email
    password: str

# Schema for Google login
class UserLoginGoogle(BaseModel):
    google_id: str

class UserLoginFacebook(BaseModel):
    facebook_id: str


# Schema to represent a user object in response
class UserSchema(BaseModel):
    id: int
    username: Optional[str]
    email: EmailStr
    latitude: Optional[float]
    longitude: Optional[float]
    profile_picture_url: Optional[str]
    role: Optional[str]
    is_super_admin: Optional[bool]
    google_id: Optional[str]
    facebook_id: Optional[str]
    created_dt: datetime

    class Config:
        from_attributes = True
