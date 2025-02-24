from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class AppointmentCreate(BaseModel):
    user_id: int
    vet_id: int
    date_time: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    status: Optional[str] = Field(
        ..., example="confirmed"
    )  # pending, confirmed, declined, reschedule_requested, completed, cancelled
    notes: Optional[str] = None
    date_time: Optional[datetime] = None  # For rescheduling

class AppointmentOut(BaseModel):
    id: uuid.UUID
    user_id: int
    vet_id: int
    date_time: datetime
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
