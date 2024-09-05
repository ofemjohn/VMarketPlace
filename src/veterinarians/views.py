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

router = APIRouter(prefix="/vet", tags=["vet"])

@router.post("/register", response_model=VeterinarianSchema, status_code=status.HTTP_201_CREATED)
async def register_veterinarian(
    veterinarian_data: VeterinarianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a new veterinarian by creating a Veterinarian record in the database.

    Parameters:
    - veterinarian_data (VeterinarianCreate): The data for creating a new veterinarian.
    - db (Session): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - VeterinarianSchema: The newly created veterinarian record.

    Raises:
    - HTTPException: If the user is already registered as a veterinarian.
    """
    existing_vet = db.query(Veterinarian).filter(Veterinarian.user_id == current_user.id).first()
    if existing_vet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already registered as a veterinarian.")

    veterinarian = create_veterinarian(db, veterinarian_data, user_id=current_user.id)

    current_user.role = UserRole.veterinarian
    db.commit()

    return veterinarian

@router.put("/update", response_model=VeterinarianSchema)
async def update_veterinarian_info(
    update_data: VeterinarianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the veterinarian's information.

    Parameters:
    - update_data (VeterinarianUpdate): The data for updating the veterinarian's information.
    - db (Session): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - VeterinarianSchema: The updated veterinarian record.

    Raises:
    - HTTPException: If the veterinarian profile is not found.
    """
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
    """
    Approves a veterinarian profile based on the provided veterinarian ID.

    This function is only accessible to admin users. It checks if the current user is an admin,
    and if so, it calls the `approve_veterinarian` service to update the veterinarian's status to approved.

    Parameters:
    - veterinarian_id (int): The ID of the veterinarian profile to be approved.
    - db (Session): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - VeterinarianSchema: The updated veterinarian record with the 'approved' status.

    Raises:
    - HTTPException: If the current user is not an admin.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can approve veterinarians")
    approved_veterinarian = approve_veterinarian(db, veterinarian_id)
    return approved_veterinarian

@router.post("/interact", response_model=UserVeterinarianSchema)
async def interact_with_veterinarian(
    interaction_data: UserVeterinarianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Records a user's interaction with a veterinarian.

    This function creates a new record in the database representing a user's interaction with a veterinarian.
    It uses the provided `interaction_data` to create a new `UserVeterinarian` record.

    Parameters:
    - interaction_data (UserVeterinarianCreate): The data for creating a new user-veterinarian interaction record.
    - db (Session): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - UserVeterinarianSchema: The newly created user-veterinarian interaction record.
    """
    interaction = create_user_veterinarian_interaction(db, current_user.id, interaction_data)
    return interaction

@router.post("/nearby", response_model=List[VeterinarianSchema])
async def get_nearby_vets(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of nearby veterinarians based on the provided geographical coordinates.

    Parameters:
    - data (dict): A dictionary containing 'latitude' and 'longitude' keys.
    - db (Session): The database session.
    - current_user (User): The currently authenticated user.

    Returns:
    - List[VeterinarianSchema]: A list of veterinarian records that are within the specified radius of the user's location.
    """
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Latitude and Longitude are required.")

    radius = 10.0  # Default radius in kilometers

    veterinarians = get_nearby_veterinarians(db, latitude, longitude, radius)
    return veterinarians

@router.post("/upload-document", status_code=status.HTTP_200_OK)
async def upload_veterinarian_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a qualification document for the veterinarian's profile.

    This function handles the upload of a qualification document for a veterinarian's profile.
    It first checks if the veterinarian profile exists for the current user. If not, it raises a 404 Not Found exception.
    Then, it calls the `upload_vet_document` service to upload the document and returns the URL of the uploaded document.

    Parameters:
    - file (UploadFile): The file to be uploaded. This parameter is expected to be a file uploaded by the user.
    - db (Session): The database session. This parameter is used to interact with the database.
    - current_user (User): The currently authenticated user. This parameter is used to identify the veterinarian's profile.

    Returns:
    - dict: A dictionary containing the URL of the uploaded qualification document. The dictionary has the following structure:
      {
        "qualification_document_url": str
      }
    """
    veterinarian = db.query(Veterinarian).filter(Veterinarian.user_id == current_user.id).first()
    if not veterinarian:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinarian profile not found")

    document_url = await upload_vet_document(veterinarian.id, file, db)
    return {"qualification_document_url": document_url}
