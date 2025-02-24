from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Base schema
class VeterinarianBase(BaseModel):
    specialty: str
    clinic_name: str
    services_offered: List[str]
    qualifications: List[str] = Field(default_factory=list)
    subscription_plan: str
    subscription_status: str

# Registration schema (input)
class VeterinarianRegister(VeterinarianBase):
    user_id: int

# Schema for updating veterinarian profile (input)
class VeterinarianUpdate(BaseModel):
    specialty: Optional[str] = None
    clinic_name: Optional[str] = None
    services_offered: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    approved: Optional[bool] = None

# Response schema
class VeterinarianOut(VeterinarianBase):
    id: int
    user_id: int
    approved: bool
    rating: float
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True
