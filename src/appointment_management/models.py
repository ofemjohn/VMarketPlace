from sqlalchemy import Column, DateTime, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from src.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vet_id = Column(ForeignKey("veterinarians.id", ondelete="CASCADE"), nullable=False)
    date_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, confirmed, declined, reschedule_requested, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    veterinarian = relationship("Veterinarian")
