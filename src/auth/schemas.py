from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime

# Schema for creating a new user
class UserCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    web_push_subscription: Optional[str] = None  # Push subscription data

# Schema for updating an existing user
class UserUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_picture_url: Optional[HttpUrl] = None
    email: Optional[EmailStr] = None
    web_push_subscription: Optional[str] = None  # Update push subscription

# Schema for user login
class UserLogin(BaseModel):
    identifier: str  # This can be either the username or email
    password: str

# Schema for password reset request
class ForgotPasswordRequest(BaseModel):
    email: EmailStr  # User's email for password reset request

3# Schema for password reset and token verification
class ResetPasswordRequest(BaseModel):
    token: str  # Token received via email
    new_password: str  # New password entered by the user

# Schema for Google login
class UserLoginGoogle(BaseModel):
    id_token: str

# Schema for Facebook login
class UserLoginFacebook(BaseModel):
    facebook_id: Optional[str] = None

# Schema to represent a user object in response
class UserSchema(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: EmailStr
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    profile_picture_url: Optional[str] = None
    role: Optional[str] = None
    is_super_admin: Optional[bool] = None
    google_id: Optional[str] = None
    facebook_id: Optional[str] = None
    web_push_subscription: Optional[str] = None  # Push notification subscription data
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True
