from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import List, Optional

class PetListingCreate(BaseModel):
    title: str
    description: str
    price: float
    location: str
    pet_type: str
    breed: str
    age: float
    sex: str
    offers_crossing_service: bool = False  # New field for crossing service

class PetListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    pet_type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[float] = None
    sex: Optional[str] = None
    offers_crossing_service: Optional[bool] = None

class PetListingSchema(BaseModel):
    id: int
    title: str
    description: str
    price: float
    location: str
    pet_type: str
    breed: str
    age: float
    sex: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    offers_crossing_service: bool
    images: List[str] = []  # URLs of images

    class Config:
        from_attributes = True

class PetImageCreate(BaseModel):
    image_url: HttpUrl

class PetImageSchema(BaseModel):
    id: int
    pet_listing_id: int
    image_url: str

    class Config:
        from_attributes = True
