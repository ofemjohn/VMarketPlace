from fastapi import APIRouter
from src.auth.views import router as auth_router
from src.veterinarian_management.view import router as veterinarians_router
# from src.petRecord.views import router as pet_records_router
# from src.petlisting.views import router as petlisting_router





router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(veterinarians_router)
# router.include_router(pet_records_router)
# router.include_router(petlisting_router)

