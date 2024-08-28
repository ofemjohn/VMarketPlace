from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean, Enum
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
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    profile_picture_url = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.user)
    created_dt = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_super_admin = Column(Boolean, default=False)  # To identify super admins
    google_id = Column(String, nullable=True)  # Store Google ID
    facebook_id = Column(String, nullable=True)  # Store Facebook ID

    # Relationships
    veterinarian = relationship("Veterinarian", back_populates="user", uselist=False)
    veterinarian_interactions = relationship("UserVeterinarian", back_populates="user")
