from fastapi import HTTPException, status, UploadFile
from firebase_admin import storage
from sqlalchemy.orm import Session
from typing import List, Optional
from src.veterinarian_management.models import Veterinarian
from src.veterinarian_management.schemas import VeterinarianRegister, VeterinarianUpdate
from datetime import datetime



ALLOWED_DOC_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}

# Register veterinarian
async def register_veterinarian(db: Session, vet: VeterinarianRegister) -> Veterinarian:
    new_vet = Veterinarian(**vet.dict())
    db.add(new_vet)
    db.commit()
    db.refresh(new_vet)
    return new_vet

# Get list of veterinarians with optional filters
async def get_veterinarians(
    db: Session, 
    specialty: Optional[str] = None,
    approved: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20
) -> List[Veterinarian]:
    query = db.query(Veterinarian)
    if specialty:
        query = query.filter(Veterinarian.specialty.ilike(f"%{specialty}%"))
    if approved is not None:
        query = query.filter(Veterinarian.approved == approved)

    return query.offset(skip).limit(limit).all()

# Fetch veterinarian details by ID
async def get_veterinarian(db: Session, vet_id: int) -> Optional[Veterinarian]:
    return db.query(Veterinarian).filter(Veterinarian.id == vet_id).first()

# Update veterinarian profile
async def update_veterinarian(db: Session, vet_id: int, updates: VeterinarianUpdate) -> Optional[Veterinarian]:
    vet = db.query(Veterinarian).filter(Veterinarian.id == vet_id).first()
    if not vet:
        return None

    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vet, key, value)

    db.commit()
    db.refresh(vet)
    return vet

# Approve veterinarian (by admin)
async def approve_veterinarian(db: Session, vet_id: int) -> Optional[Veterinarian]:
    vet = db.query(Veterinarian).filter(Veterinarian.id == vet_id).first()
    if not vet:
        return None

    vet.approved = True
    db.commit()
    db.refresh(vet)
    return vet


async def upload_qualification_documents(
    db: Session, vet_id: int, files: List[UploadFile]
) -> List[str]:
    vet = db.query(Veterinarian).filter(Veterinarian.id == vet_id).first()
    if not vet:
        raise HTTPException(status_code=404, detail="Veterinarian not found")

    bucket = storage.bucket()
    uploaded_urls = []

    for file in files:
        if file.content_type not in ALLOWED_DOC_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.content_type}. Allowed types: JPG, PNG, JPEG, PDF"
            )

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        extension = file.filename.split('.')[-1]
        unique_filename = f"{vet_id}_qualification_{timestamp}.{extension}"
        blob = bucket.blob(f"qualifications/{unique_filename}")

        try:
            blob.upload_from_file(file.file, content_type=file.content_type)
            blob.make_public()
            uploaded_urls.append(blob.public_url)
            print(f"Uploaded and made public: {blob.public_url}")  # Debug print
        except Exception as e:
            print(f"Firebase upload error: {e}")  # Debug print
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {file.filename}. Error: {e}"
            )

    # Initialize if needed
    if vet.qualifications is None:
        print("Qualifications was None, initializing as empty list.")  # Debug print
        vet.qualifications = []

    # Extend and check if added correctly
    vet.qualifications.extend(uploaded_urls)
    print("Current qualifications list:", vet.qualifications)  # Debug print

    # Explicitly flagging the field as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(vet, "qualifications")

    db.add(vet)  # Explicitly add the object back to the session
    db.commit()
    db.refresh(vet)

    print("After commit and refresh:", vet.qualifications)  # Debug print

    return uploaded_urls

