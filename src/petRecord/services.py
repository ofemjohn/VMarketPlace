from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.petRecord.models import PetRecord
from src.petRecord.schemas import PetRecordCreate, PetRecordUpdate
from src.appointments.models import Appointment
from src.appointments.services import send_notification
from typing import List

def create_pet_record(db: Session, veterinarian_id: int, appointment_id: int, pet_record_data: PetRecordCreate) -> PetRecord:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.veterinarian_id == veterinarian_id).first()
    if not appointment:
        raise HTTPException(status_code=403, detail="You are not authorized to create a record for this pet.")

    pet_record = PetRecord(
        pet_name=pet_record_data.pet_name,
        pet_type=pet_record_data.pet_type,
        breed=pet_record_data.breed,
        age=pet_record_data.age,
        weight=pet_record_data.weight,
        sex=pet_record_data.sex,
        veterinarian_id=veterinarian_id,
        appointment_id=appointment_id,
        condition=pet_record_data.condition,
        symptoms=pet_record_data.symptoms,
        treatment=pet_record_data.treatment,
        medications=pet_record_data.medications,
        vaccinations=pet_record_data.vaccinations,
        procedures=pet_record_data.procedures,
        follow_up_date=pet_record_data.follow_up_date,
        additional_notes=pet_record_data.additional_notes
    )
    db.add(pet_record)
    db.commit()
    db.refresh(pet_record)

    send_notification(
        title="New Pet Record Created",
        body=f"A new record has been created for your pet {pet_record.pet_name}.",
        recipient_user_id=appointment.user_id,
        db=db
    )

    return pet_record

def update_pet_record(db: Session, pet_record_id: int, pet_record_data: PetRecordUpdate, veterinarian_id: int) -> PetRecord:
    pet_record = db.query(PetRecord).filter(PetRecord.id == pet_record_id, PetRecord.veterinarian_id == veterinarian_id).first()
    if not pet_record:
        raise HTTPException(status_code=404, detail="Pet record not found")

    for key, value in pet_record_data.dict(exclude_unset=True).items():
        setattr(pet_record, key, value)
    
    db.commit()
    db.refresh(pet_record)

    send_notification(
        title="Pet Record Updated",
        body=f"The record for your pet {pet_record.pet_name} has been updated.",
        recipient_user_id=pet_record.appointment.user_id,
        db=db
    )
    
    return pet_record

def get_pet_record_by_id(db: Session, pet_record_id: int) -> PetRecord:
    pet_record = db.query(PetRecord).filter(PetRecord.id == pet_record_id).first()
    if not pet_record:
        raise HTTPException(status_code=404, detail="Pet record not found")
    return pet_record

def get_pet_records_for_user(db: Session, user_id: int) -> List[PetRecord]:
    return db.query(PetRecord).join(Appointment).filter(Appointment.user_id == user_id).all()

def get_pet_records_for_veterinarian(db: Session, veterinarian_id: int) -> List[PetRecord]:
    return db.query(PetRecord).filter(PetRecord.veterinarian_id == veterinarian_id).all()
