from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class PetRecordCreate(BaseModel):
    pet_name: str
    pet_type: str
    breed: str
    age: float
    weight: float
    sex: str
    condition: str
    symptoms: Optional[str] = None
    treatment: str
    medications: Optional[str] = None
    vaccinations: Optional[str] = None
    procedures: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    additional_notes: Optional[str] = None

class PetRecordUpdate(BaseModel):
    condition: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    medications: Optional[str] = None
    vaccinations: Optional[str] = None
    procedures: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    additional_notes: Optional[str] = None

class PetRecordSchema(BaseModel):
    id: int
    pet_name: str
    pet_type: str
    breed: str
    age: float
    weight: float
    sex: str
    veterinarian_id: int
    appointment_id: int
    condition: str
    symptoms: Optional[str] = None
    treatment: str
    medications: Optional[str] = None
    vaccinations: Optional[str] = None
    procedures: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    additional_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
