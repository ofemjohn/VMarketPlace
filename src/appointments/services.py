import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from src.appointments.models import Appointment
from src.appointments.schemas import AppointmentCreate, AppointmentUpdate
from src.auth.models import User
from datetime import datetime, timedelta
import threading
from exponent_server_sdk import PushClient, PushMessage, PushServerError, DeviceNotRegisteredError

def create_appointment(db: Session, user_id: int, appointment_data: AppointmentCreate, creator_role: str) -> Appointment:
    appointment = Appointment(
        user_id=user_id,
        veterinarian_id=appointment_data.veterinarian_id,
        appointment_date=appointment_data.appointment_date,
        notes=appointment_data.notes,
        phone_number=appointment_data.phone_number,
        status="pending" if creator_role == 'user' else "approved"  
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Send notification to the veterinarian about the new appointment if created by the user
    if creator_role == 'user':
        send_notification(
            title="New Appointment Request",
            body=f"New appointment on {appointment.appointment_date}",
            recipient_user_id=appointment.veterinarian_id,
            db=db
        )

    # Send notification to the user if the appointment is created by the veterinarian
    if creator_role == 'veterinarian':
        send_notification(
            title="Appointment Booked",
            body=f"Your appointment with the veterinarian on {appointment.appointment_date} is confirmed.",
            recipient_user_id=appointment.user_id,
            db=db
        )

    # Schedule a reminder 1 day before the appointment date
    schedule_reminder(appointment, db)
    
    return appointment

def update_appointment(db: Session, appointment_id: int, appointment_data: AppointmentUpdate, updater_id: int, updater_role: str) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    for key, value in appointment_data.dict(exclude_unset=True).items():
        setattr(appointment, key, value)
    
    db.commit()
    db.refresh(appointment)

    recipient_id = appointment.user_id if updater_role == 'veterinarian' else appointment.veterinarian_id
    
    try:
        send_notification(
            title="Appointment Updated",
            body=f"Your appointment on {appointment.appointment_date} has been updated.",
            recipient_user_id=recipient_id,
            db=db
        )
    except Exception as e:
        print(f"Notification sending failed: {e}")

    return appointment

def get_appointment_by_id(db: Session, appointment_id: int) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

def get_user_appointments(db: Session, user_id: int) -> List[Appointment]:
    return db.query(Appointment).filter(Appointment.user_id == user_id).all()

def get_veterinarian_appointments(db: Session, veterinarian_id: int) -> List[Appointment]:
    return db.query(Appointment).filter(Appointment.veterinarian_id == veterinarian_id).all()

def send_notification(title: str, body: str, recipient_user_id: int, db: Session):
    user = db.query(User).filter(User.id == recipient_user_id).first()
    if not user or not user.expo_push_token:
        return  

    message = PushMessage(
        to=user.expo_push_token,
        title=title,
        body=body,
        data={"extra": "data"}  
    )

    try:
        response = PushClient().publish(message)
        response.validate_response() 
    except DeviceNotRegisteredError:
        user.expo_push_token = None
        db.commit()
    except PushServerError as exc:
        print(f"Push server error: {exc}")
    except Exception as e:
        print(f"Failed to send notification: {str(e)}")

def schedule_reminder(appointment: Appointment, db: Session):
    def send_reminder():
        send_notification(
            title="Appointment Reminder",
            body=f"Reminder: You have an appointment on {appointment.appointment_date}",
            recipient_user_id=appointment.user_id,
            db=db
        )
    delay = (appointment.appointment_date - timedelta(days=1)) - datetime.now()
    if delay.total_seconds() > 0:
        threading.Timer(delay.total_seconds(), send_reminder).start()

def cancel_appointment(db: Session, appointment_id: int, current_user: User):
    appointment = get_appointment_by_id(db, appointment_id)

    if current_user.id == appointment.user_id:
        recipient_id = appointment.veterinarian_id
        canceled_by = "User"
    else:
        recipient_id = appointment.user_id
        canceled_by = "Veterinarian"

    send_notification(
        title="Appointment Canceled",
        body=f"The appointment on {appointment.appointment_date} was canceled by the {canceled_by}.",
        recipient_user_id=recipient_id,
        db=db
    )

    db.delete(appointment)
    db.commit()
