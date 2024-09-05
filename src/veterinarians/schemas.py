from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class VeterinarianCreate(BaseModel):
    clinic_name: str = Field(..., max_length=255)
    specialty: List[str] = Field(..., description="List of specialties the veterinarian has")
    services_offered: Optional[List[str]] = Field(None, description="List of services offered by the veterinarian")
    latitude: float
    longitude: float

class VeterinarianUpdate(BaseModel):
    clinic_name: Optional[str] = Field(None, max_length=255)
    specialty: Optional[List[str]] = Field(None, description="List of specialties the veterinarian has")
    services_offered: Optional[List[str]] = Field(None, description="List of services offered by the veterinarian")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    approved: Optional[bool] = None

class VeterinarianSchema(BaseModel):
    id: int
    user_id: int
    clinic_name: Optional[str] = None
    specialty: List[str] = []  # Returning a list of specialties
    services_offered: List[str] = []  # Returning a list of services offered
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
        form_attributes = True
