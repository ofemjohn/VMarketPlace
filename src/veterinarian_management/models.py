from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, ARRAY, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Veterinarian(Base):
    __tablename__ = "veterinarians"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    specialty = Column(String, index=True, nullable=False)
    clinic_name = Column(String, index=True, nullable=False)
    services_offered = Column(ARRAY(String), nullable=False)
    qualifications = Column(ARRAY(String), nullable=False, default=list)
    approved = Column(Boolean, default=False)
    subscription_plan = Column(String, nullable=False)
    subscription_status = Column(String, nullable=False)
    rating = Column(Float, default=0)
    created_dt = Column(DateTime, default=datetime.utcnow)
    updated_dt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Add relationship to User
    user = relationship("User", back_populates="veterinarian_profile")