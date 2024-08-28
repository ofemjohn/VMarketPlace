from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Veterinarian(Base):
    __tablename__ = "veterinarians"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    clinic_name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    services_offered = Column(String, nullable=True)
    qualification_document = Column(String, nullable=True)
    approved = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="veterinarian")
    user_interactions = relationship("UserVeterinarian", back_populates="veterinarian")


class UserVeterinarian(Base):
    __tablename__ = "user_veterinarians"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    interaction_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)  # Optional field for interaction notes

    # Relationships
    user = relationship("User", back_populates="veterinarian_interactions")
    veterinarian = relationship("Veterinarian", back_populates="user_interactions")
