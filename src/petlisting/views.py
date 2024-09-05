from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from src.database import get_db
from src.auth.services import get_current_user
from src.petlisting.schemas import PetListingCreate, PetListingUpdate, PetListingSchema, PetImageSchema
from src.petlisting.services import (
    create_pet_listing,
    update_pet_listing,
    get_pet_listing_by_id,
    search_pet_listings,
    add_pet_images
)
from src.auth.models import User

router = APIRouter(prefix="/listings", tags=["listings"])

@router.post("/", response_model=PetListingSchema, status_code=status.HTTP_201_CREATED)
async def create_pet_listing_route(
    pet_listing_data: PetListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_pet_listing(db, pet_listing_data, current_user.id)

@router.put("/{listing_id}", response_model=PetListingSchema)
async def update_pet_listing_route(
    listing_id: int,
    pet_listing_data: PetListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_pet_listing(db, listing_id, pet_listing_data, current_user.id)

@router.get("/{listing_id}", response_model=PetListingSchema)
async def get_pet_listing_route(
    listing_id: int,
    db: Session = Depends(get_db)
):
    return get_pet_listing_by_id(db, listing_id)

@router.get("/search", response_model=List[PetListingSchema])
async def search_pet_listings_route(
    search_term: str,
    db: Session = Depends(get_db)
):
    return search_pet_listings(db, search_term)

@router.post("/{listing_id}/images/", response_model=List[PetImageSchema])
async def add_pet_images_route(
    listing_id: int,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return add_pet_images(db, listing_id, images)
