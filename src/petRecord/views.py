from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.auth.services import get_current_user
from src.petRecord.schemas import PetRecordCreate, PetRecordUpdate, PetRecordSchema
from src.petRecord.services import (
    create_pet_record,
    update_pet_record,
    get_pet_record_by_id,
    get_pet_records_for_user,
    get_pet_records_for_veterinarian
)

router = APIRouter(prefix="/pet-records", tags=["pet-records"])

@router.post("/", response_model=PetRecordSchema, status_code=status.HTTP_201_CREATED)
async def create_pet_record_route(
    pet_record_data: PetRecordCreate,
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != 'veterinarian':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only veterinarians can create pet records")
    
    return create_pet_record(db, current_user.id, appointment_id, pet_record_data)

@router.put("/{pet_record_id}", response_model=PetRecordSchema)
async def update_pet_record_route(
    pet_record_id: int,
    pet_record_data: PetRecordUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != 'veterinarian':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only veterinarians can update pet records")
    
    return update_pet_record(db, pet_record_id, pet_record_data, current_user.id)

@router.get("/{pet_record_id}", response_model=PetRecordSchema)
async def get_pet_record_route(
    pet_record_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    pet_record = get_pet_record_by_id(db, pet_record_id)
    if pet_record.appointment.user_id != current_user.id and pet_record.veterinarian_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this pet record")
    return pet_record

@router.get("/", response_model=List[PetRecordSchema])
async def list_user_pet_records(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role == 'veterinarian':
        return get_pet_records_for_veterinarian(db, current_user.id)
    return get_pet_records_for_user(db, current_user.id)
