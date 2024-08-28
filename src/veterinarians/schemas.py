from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VeterinarianCreate(BaseModel):
    clinic_name: Optional[str] = Field(..., max_length=255)
    specialty: Optional[str] = Field(..., max_length=255)
    services_offered: Optional[str] = None
    latitude: Optional[str] = float
    longitude: Optional[str] = float

class VeterinarianUpdate(BaseModel):
    clinic_name: Optional[str] = Field(None, max_length=255)
    specialty: Optional[str] = Field(None, max_length=255)
    services_offered: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    approved: Optional[bool] = None

class VeterinarianSchema(BaseModel):
    id: int
    user_id: int
    clinic_name: Optional[str] = None
    specialty: Optional[str] = None
    services_offered: Optional[str] = None
    qualification_document: Optional[str] = None
    approved: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserVeterinarianCreate(BaseModel):
    veterinarian_id: int
    notes: Optional[str] = None

class UserVeterinarianSchema(BaseModel):
    id: int
    user_id: int
    veterinarian_id: int
    interaction_date: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
