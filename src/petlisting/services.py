from sqlalchemy.orm import Session
from src.petlisting.models import PetListing, PetImage
from src.petlisting.schemas import PetListingCreate, PetListingUpdate, PetImageCreate
from fastapi import HTTPException, status, UploadFile, File
from typing import List
import firebase_admin
from firebase_admin import storage
from uuid import uuid4

def create_pet_listing(db: Session, pet_listing_data: PetListingCreate, user_id: int) -> PetListing:
    pet_listing = PetListing(**pet_listing_data.dict(), user_id=user_id)
    db.add(pet_listing)
    db.commit()
    db.refresh(pet_listing)
    return pet_listing

def update_pet_listing(db: Session, listing_id: int, pet_listing_data: PetListingUpdate, user_id: int) -> PetListing:
    pet_listing = db.query(PetListing).filter(PetListing.id == listing_id, PetListing.user_id == user_id).first()
    if not pet_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet listing not found")

    for key, value in pet_listing_data.dict(exclude_unset=True).items():
        setattr(pet_listing, key, value)
    
    db.commit()
    db.refresh(pet_listing)
    return pet_listing

def get_pet_listing_by_id(db: Session, listing_id: int) -> PetListing:
    pet_listing = db.query(PetListing).filter(PetListing.id == listing_id).first()
    if not pet_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet listing not found")
    return pet_listing

def search_pet_listings(db: Session, search_term: str) -> List[PetListing]:
    return db.query(PetListing).filter(
        PetListing.title.ilike(f"%{search_term}%") | 
        PetListing.description.ilike(f"%{search_term}%") | 
        PetListing.breed.ilike(f"%{search_term}%")
    ).all()

def upload_image_to_firebase(image: UploadFile) -> str:
    # Generate a unique filename using uuid4
    filename = f"{uuid4()}.{image.filename.split('.')[-1]}"
    
    # Initialize Firebase Storage bucket
    bucket = storage.bucket()
    
    # Upload the image
    blob = bucket.blob(filename)
    blob.upload_from_file(image.file, content_type=image.content_type)
    
    # Make the URL publicly accessible
    blob.make_public()
    
    # Return the URL of the uploaded image
    return blob.public_url

def add_pet_images(db: Session, pet_listing_id: int, images: List[UploadFile]) -> List[PetImage]:
    pet_listing = db.query(PetListing).filter(PetListing.id == pet_listing_id).first()
    if not pet_listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet listing not found")

    pet_images = []
    for image in images:
        image_url = upload_image_to_firebase(image)
        pet_image = PetImage(pet_listing_id=pet_listing_id, image_url=image_url)
        db.add(pet_image)
        db.commit()
        db.refresh(pet_image)
        pet_images.append(pet_image)

    return pet_images
