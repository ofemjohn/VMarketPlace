from fastapi import APIRouter
from src.auth.views import router as auth_router
from src.veterinarians.views import router as veterinarians_router
from src.appointments.views import router as appointments_router
from src.petRecord.views import router as pet_records_router
from src.petlisting.views import router as pet_listing_router
from src.chat.views import router as chat_router




router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(veterinarians_router)
router.include_router(appointments_router)
router.include_router(pet_records_router)
router.include_router(pet_listing_router)
router.include_router(chat_router)
