from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from src.database import get_db
from .schemas import AppointmentCreate, AppointmentUpdate, AppointmentOut
from . import services
from src.auth.services import get_current_user
from src.auth.models import User, UserRole
import json

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != appointment.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await services.create_appointment(db, appointment)

@router.get("/", response_model=List[AppointmentOut])
async def get_appointments(
    user_id: Optional[int] = None,
    vet_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.user and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == UserRole.veterinarian and current_user.id != vet_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await services.list_appointments(db, user_id, vet_id)

@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    updates: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = await services.get_appointment_by_id(db, appointment_id)

    if current_user.role == UserRole.veterinarian and current_user.id != appointment.vet_id:
        raise HTTPException(status_code=403, detail="Not authorized as veterinarian")
    if updates.status == "cancelled" and current_user.id != appointment.user_id:
        raise HTTPException(status_code=403, detail="Only the appointment owner can cancel the appointment")

    return await services.update_appointment(db, appointment_id, updates)

@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await services.cancel_appointment(db, appointment_id)
