from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from src.veterinarians.schemas import (
    VeterinarianCreate,
    VeterinarianUpdate,
    VeterinarianSchema,
    UserVeterinarianCreate,
    UserVeterinarianSchema
)
from src.veterinarians.services import (
    create_veterinarian,
    update_veterinarian,
    approve_veterinarian,
    create_user_veterinarian_interaction,
    get_nearby_veterinarians,
    upload_vet_document
)
from src.auth.models import User, UserRole
from src.database import get_db
from src.auth.services import get_current_user
from src.veterinarians.models import Veterinarian

router = APIRouter()

@router.post("/register", response_model=VeterinarianSchema, status_code=status.HTTP_201_CREATED)
async def register_veterinarian(
    veterinarian_data: VeterinarianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if the user is already registered as a veterinarian
    existing_vet = db.query(Veterinarian).filter(Veterinarian.user_id == current_user.id).first()
    if existing_vet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already registered as a veterinarian.")
    
    # Register the user as a veterinarian
    veterinarian = create_veterinarian(db, veterinarian_data, user_id=current_user.id)
    
    # Update user role to 'veterinarian'
    current_user.role = UserRole.veterinarian
    db.commit()
    
    return veterinarian


@router.put("/update", response_model=VeterinarianSchema)
async def update_veterinarian_info(
    update_data: VeterinarianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    veterinarian = db.query(Veterinarian).filter(Veterinarian.user_id == current_user.id).first()
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian profile not found")
    updated_veterinarian = update_veterinarian(db, veterinarian, update_data)
    return updated_veterinarian

@router.post("/{veterinarian_id}/approve", response_model=VeterinarianSchema)
async def approve_veterinarian_route(
    veterinarian_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user or current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can approve veterinarians")
    approved_veterinarian = approve_veterinarian(db, veterinarian_id)
    return approved_veterinarian

@router.post("/interact", response_model=UserVeterinarianSchema)
async def interact_with_veterinarian(
    interaction_data: UserVeterinarianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    interaction = create_user_veterinarian_interaction(db, current_user.id, interaction_data)
    return interaction

@router.get("/nearby", response_model=List[VeterinarianSchema])
async def get_nearby_vets(
    latitude: float,
    longitude: float,
    radius: float = 10.0,
    db: Session = Depends(get_db)
):
    veterinarians = get_nearby_veterinarians(db, latitude, longitude, radius)
    return veterinarians

@router.post("/upload-document/{vet_id}", status_code=status.HTTP_200_OK)
async def upload_veterinarian_document(
    vet_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure the current user is an admin or the veterinarian themselves
    veterinarian = db.query(Veterinarian).filter(Veterinarian.id == vet_id, Veterinarian.user_id == current_user.id).first()
    if not veterinarian and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to upload this document.")
    
    document_url = await upload_vet_document(vet_id, file, db)
    return {"qualification_document_url": document_url}
