from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AppointmentCreate(BaseModel):
    veterinarian_id: int
    appointment_date: datetime  # Required field for both date and time
    notes: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=15, description="User's phone number for contact")

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class AppointmentSchema(BaseModel):
    id: int
    user_id: int
    veterinarian_id: int
    appointment_date: datetime
    notes: Optional[str] = None
    phone_number: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
