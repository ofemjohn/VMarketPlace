from sqlalchemy.orm import Session
from typing import List, Optional
from .models import Appointment
from .schemas import AppointmentCreate, AppointmentUpdate
from fastapi import HTTPException, status
import uuid
from src.web_push_utils import send_web_push
import json
from src.auth.models import User

async def create_appointment(db: Session, appointment: AppointmentCreate) -> Appointment:
    new_appointment = Appointment(**appointment.dict())
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    user = db.query(User).get(new_appointment.user_id)
    vet = db.query(User).get(new_appointment.vet_id)

    message_user = f"Your appointment is scheduled for {new_appointment.date_time.strftime('%Y-%m-%d %H:%M')}."
    message_vet = f"New appointment request for {new_appointment.date_time.strftime('%Y-%m-%d %H:%M')}."

    if user.web_push_subscription:
        await send_web_push(json.loads(user.web_push_subscription), message_user)
    if vet.web_push_subscription:
        await send_web_push(json.loads(vet.web_push_subscription), message_vet)

    return new_appointment

async def list_appointments(db: Session, user_id: Optional[int] = None, vet_id: Optional[int] = None) -> List[Appointment]:
    query = db.query(Appointment)
    if user_id:
        query = query.filter(Appointment.user_id == user_id)
    if vet_id:
        query = query.filter(Appointment.vet_id == vet_id)
    return query.order_by(Appointment.date_time.desc()).all()

async def get_appointment_by_id(db: Session, appointment_id: uuid.UUID) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

async def update_appointment(db: Session, appointment_id: uuid.UUID, updates: AppointmentUpdate) -> Appointment:
    appointment = await get_appointment_by_id(db, appointment_id)

    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)

    user = db.query(User).get(appointment.user_id)

    notification_message = {
        "confirmed": f"Your appointment on {appointment.date_time.strftime('%Y-%m-%d %H:%M')} is confirmed.",
        "declined": "Your appointment has been declined by the veterinarian.",
        "reschedule_requested": f"Vet requested reschedule: {appointment.date_time.strftime('%Y-%m-%d %H:%M')}.",
        "cancelled": "Your appointment has been cancelled."
    }.get(appointment.status, "Appointment updated.")

    if user.web_push_subscription:
        await send_web_push(json.loads(user.web_push_subscription), notification_message)

    return appointment

async def cancel_appointment(db: Session, appointment_id: uuid.UUID):
    appointment = await get_appointment_by_id(db, appointment_id)
    db.delete(appointment)
    db.commit()
