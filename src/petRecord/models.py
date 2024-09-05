from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class PetRecord(Base):
    __tablename__ = "pet_records"

    id = Column(Integer, primary_key=True, index=True)
    pet_name = Column(String, nullable=False)  # Name of the pet
    pet_type = Column(String, nullable=False)  # Type of pet (dog, cat, etc.)
    breed = Column(String, nullable=False)  # Breed of the pet
    age = Column(Float, nullable=False)  # Age of the pet in years
    weight = Column(Float, nullable=False)  # Weight of the pet in kg
    sex = Column(String, nullable=False)  # Sex of the pet (Male/Female)
    
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Add this line to establish the relationship

    condition = Column(Text, nullable=False)  # Diagnosed condition
    symptoms = Column(Text, nullable=True)  # Symptoms observed
    treatment = Column(Text, nullable=False)  # Treatment administered
    medications = Column(Text, nullable=True)  # Medications prescribed/administered
    vaccinations = Column(Text, nullable=True)  # Vaccinations given
    procedures = Column(Text, nullable=True)  # Medical procedures performed
    
    follow_up_date = Column(DateTime, nullable=True)  # Next follow-up date
    additional_notes = Column(Text, nullable=True)  # Additional notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    veterinarian = relationship("Veterinarian", back_populates="pet_records")
    appointment = relationship("Appointment", back_populates="pet_record")
    user = relationship("User", back_populates="pet_records")  # Relationship with User
