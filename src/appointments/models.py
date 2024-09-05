from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    veterinarian_id = Column(Integer, ForeignKey("veterinarians.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)  # Date and time for the appointment
    notes = Column(Text, nullable=True)
    phone_number = Column(String, nullable=True)  # Phone number for contact
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="appointments")
    veterinarian = relationship("Veterinarian", back_populates="appointments")
    pet_record = relationship("PetRecord", back_populates="appointment", uselist=False)
