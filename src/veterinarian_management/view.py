from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.veterinarian_management.schemas import (
    VeterinarianRegister, VeterinarianOut, VeterinarianUpdate
)
from src.veterinarian_management import services
from src.auth.services import get_current_user
from src.auth.models import User, UserRole

router = APIRouter(prefix="/veterinarians", tags=["veterinarians"])

# Veterinarian Registration
@router.post("/register", response_model=VeterinarianOut, status_code=status.HTTP_201_CREATED)
async def register_vet(
    vet: VeterinarianRegister, 
    db: Session = Depends(get_db)
):
    return await services.register_veterinarian(db, vet)

# List veterinarians (with filters)
@router.get("/", response_model=List[VeterinarianOut])
async def list_vets(
    specialty: str = None,
    approved: bool = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return await services.get_veterinarians(db, specialty, approved, skip, limit)

# Fetch veterinarian details
@router.get("/{vet_id}", response_model=VeterinarianOut)
async def vet_details(vet_id: int, db: Session = Depends(get_db)):
    vet = await services.get_veterinarian(db, vet_id)
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return vet

# Update veterinarian profile
@router.put("/{vet_id}", response_model=VeterinarianOut)
async def update_vet(
    vet_id: int, 
    updates: VeterinarianUpdate, 
    db: Session = Depends(get_db)
):
    vet = await services.update_veterinarian(db, vet_id, updates)
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return vet

# Approve veterinarian (only admins can perform this)
@router.post("/{vet_id}/approve", response_model=VeterinarianOut)
async def approve_vet(
    vet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can approve veterinarians")

    vet = await services.approve_veterinarian(db, vet_id)
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinarian not found")
    return vet


@router.post("/{vet_id}/upload-qualifications", status_code=200)
async def upload_qualifications(
    vet_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vet = await services.get_veterinarian(db, vet_id)
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinarian not found")

    if current_user.id != vet.user_id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Unauthorized to upload qualifications")

    uploaded_urls = await services.upload_qualification_documents(db, vet_id, files)
    return {"uploaded_documents": uploaded_urls}