from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
from geopy.distance import geodesic
from firebase_admin import storage
from typing import List
from src.veterinarians.models import Veterinarian, UserVeterinarian
from src.veterinarians.schemas import VeterinarianCreate, VeterinarianUpdate, UserVeterinarianCreate
import logging

ALLOWED_DOC_TYPES = {"application/pdf", "image/jpeg", "image/png"}

def create_veterinarian(db: Session, veterinarian_data: VeterinarianCreate, user_id: int) -> Veterinarian:
    existing_vet = db.query(Veterinarian).filter(Veterinarian.user_id == user_id).first()
    if existing_vet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered as a veterinarian.")

    veterinarian = Veterinarian(
        clinic_name=veterinarian_data.clinic_name,
        specialty=veterinarian_data.specialty,
        services_offered=veterinarian_data.services_offered,
        latitude=veterinarian_data.latitude,
        longitude=veterinarian_data.longitude,
        user_id=user_id
    )
    db.add(veterinarian)
    db.commit()
    db.refresh(veterinarian)
    return veterinarian

def update_veterinarian(db: Session, veterinarian: Veterinarian, update_data: VeterinarianUpdate) -> Veterinarian:
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(veterinarian, key, value)
    db.commit()
    db.refresh(veterinarian)
    return veterinarian

def approve_veterinarian(db: Session, veterinarian_id: int) -> Veterinarian:
    veterinarian = db.query(Veterinarian).filter(Veterinarian.id == veterinarian_id).first()
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian not found")
    veterinarian.approved = True
    db.commit()
    db.refresh(veterinarian)
    return veterinarian

def create_user_veterinarian_interaction(db: Session, user_id: int, interaction_data: UserVeterinarianCreate) -> UserVeterinarian:
    veterinarian = db.query(Veterinarian).filter(Veterinarian.id == interaction_data.veterinarian_id, Veterinarian.approved == True).first()
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian not found or not approved")

    user_vet_interaction = UserVeterinarian(
        user_id=user_id,
        veterinarian_id=interaction_data.veterinarian_id,
        notes=interaction_data.notes
    )
    db.add(user_vet_interaction)
    db.commit()
    db.refresh(user_vet_interaction)
    return user_vet_interaction

def get_nearby_veterinarians(db: Session, latitude: float, longitude: float, radius: float = 10.0) -> List[Veterinarian]:
    user_location = (latitude, longitude)
    all_vets = db.query(Veterinarian).filter(Veterinarian.approved == True).all()

    nearby_vets = []
    for vet in all_vets:
        if vet.latitude is None or vet.longitude is None:
            continue  # Skip vets with missing coordinates

        vet_location = (vet.latitude, vet.longitude)
        distance = geodesic(user_location, vet_location).kilometers

        if distance <= radius:
            nearby_vets.append(vet)

    return nearby_vets


async def upload_vet_document(vet_id: int, file: UploadFile, db: Session) -> str:
    if file.content_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document format. Only .pdf, .jpg, and .png are allowed.")

    bucket = storage.bucket()
    veterinarian = db.query(Veterinarian).filter(Veterinarian.id == vet_id).first()
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian not found")

    if veterinarian.qualification_document:
        blob_name = veterinarian.qualification_document.split("/")[-1]
        old_blob = bucket.blob(f"vet_documents/{blob_name}")
        if old_blob.exists():
            old_blob.delete()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    extension = file.filename.split('.')[-1]
    unique_filename = f"{vet_id}_{timestamp}.{extension}"

    blob = bucket.blob(f"vet_documents/{unique_filename}")

    try:
        blob.upload_from_file(file.file)
        blob.make_public()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload document. Please try again later.")

    veterinarian.qualification_document = blob.public_url
    db.commit()
    db.refresh(veterinarian)

    return blob.public_url
