from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class PetListing(Base):
    __tablename__ = "pet_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    pet_type = Column(String, nullable=False)  # e.g., Dog, Cat
    breed = Column(String, nullable=False)
    age = Column(Float, nullable=False)  # Age in years
    sex = Column(String, nullable=False)  # Male/Female
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    offers_crossing_service = Column(Boolean, default=False)  # New field for crossing service

    user = relationship("User", back_populates="pet_listings")
    images = relationship("PetImage", back_populates="pet_listing")
    chat_rooms = relationship("ChatRoom", back_populates="listing")  # Ensure this relationship is defined



class PetImage(Base):
    __tablename__ = "pet_images"

    id = Column(Integer, primary_key=True, index=True)
    pet_listing_id = Column(Integer, ForeignKey("pet_listings.id"), nullable=False)
    image_url = Column(String, nullable=False)

    pet_listing = relationship("PetListing", back_populates="images")
