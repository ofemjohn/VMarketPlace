from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.auth.services import get_current_user
from src.appointments.schemas import AppointmentCreate, AppointmentUpdate, AppointmentSchema
from src.appointments.services import (
    create_appointment,
    update_appointment,
    get_appointment_by_id,
    get_user_appointments,
    get_veterinarian_appointments,
    cancel_appointment,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Book an appointment (User or Veterinarian)
@router.post("/", response_model=AppointmentSchema, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    creator_role = 'veterinarian' if current_user.role == 'veterinarian' else 'user'
    return create_appointment(db, current_user.id, appointment_data, creator_role)

# Update an appointment (User can update their appointment, Veterinarian can approve/decline)
@router.put("/{appointment_id}", response_model=AppointmentSchema)
async def update_appointment_route(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    appointment = get_appointment_by_id(db, appointment_id)

    if current_user.id != appointment.user_id and current_user.id != appointment.veterinarian_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this appointment")
    
    updater_role = 'veterinarian' if current_user.id == appointment.veterinarian_id else 'user'
    return update_appointment(db, appointment_id, appointment_data, updater_id=current_user.id, updater_role=updater_role)

# List all appointments for the current user
@router.get("/", response_model=List[AppointmentSchema])
async def list_user_appointments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role == 'veterinarian':
        return get_veterinarian_appointments(db, current_user.id)
    return get_user_appointments(db, current_user.id)

# Get details of a specific appointment
@router.get("/{appointment_id}", response_model=AppointmentSchema)
async def get_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    appointment = get_appointment_by_id(db, appointment_id)
    if appointment.user_id != current_user.id and appointment.veterinarian_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this appointment")
    return appointment

# Cancel an appointment (User or Veterinarian can cancel the appointment)
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment_route(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    cancel_appointment(db, appointment_id, current_user)
    return {"detail": "Appointment canceled successfully"}
