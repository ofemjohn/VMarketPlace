from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, Enum, Text
from datetime import datetime
from sqlalchemy.orm import relationship
from src.database import Base
import enum

class UserRole(enum.Enum):
    user = "user"
    veterinarian = "veterinarian"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    profile_picture_url = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.user)
    created_dt = Column(DateTime, default=datetime.utcnow)
    updated_dt = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_super_admin = Column(Boolean, default=False)
    google_id = Column(String, nullable=True)
    facebook_id = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    web_push_subscription = Column(Text, nullable=True)

    # ✅ Add relationship to Veterinarian
    veterinarian_profile = relationship(
        "Veterinarian", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )