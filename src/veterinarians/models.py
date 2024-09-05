from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Veterinarian(Base):
    __tablename__ = "veterinarians"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    clinic_name = Column(String, nullable=False)
    specialty = Column(JSON, nullable=False)  # Stored as a JSON list
    services_offered = Column(JSON, nullable=True) 
    qualification_document = Column(String, nullable=True)
    approved = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="veterinarian")
    user_interactions = relationship("UserVeterinarian", back_populates="veterinarian")
    appointments = relationship("Appointment", back_populates="veterinarian")
    pet_records = relationship("PetRecord", back_populates="veterinarian")
    chat_rooms = relationship("ChatRoom", back_populates="veterinarian")  # Add this line




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
