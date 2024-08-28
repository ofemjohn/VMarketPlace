from fastapi import APIRouter
from src.auth.views import router as auth_router
from src.veterinarians.views import router as veterinarians_router


router = APIRouter(prefix="/v1")

router.include_router(auth_router)
router.include_router(veterinarians_router, prefix="/v1")
