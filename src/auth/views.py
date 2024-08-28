from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import List, Dict
from src.auth.schemas import UserCreate, UserUpdate, UserLogin, UserLoginGoogle, UserLoginFacebook
from src.database import get_db
from fastapi.security import OAuth2PasswordBearer
from src.auth.services import (
    google_auth, 
    existing_user_by_email, 
    create_access_token, 
    create_refresh_token, 
    get_current_user, 
    authenticate, 
    update_user,
    refresh_access_token,
    create_user as create_new_user,
    upload_profile_picture,
    get_user_by_email,
    get_all_users,
    facebook_auth
)
from src.auth.models import User, UserRole  # Import User and UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize the OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User Registration Route
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_user(user: UserCreate, db: Session = Depends(get_db)) -> Dict:
    if await existing_user_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    # Create a new user with the default role as 'user'
    db_user = await create_new_user(db, user, role=UserRole.user)
    access_token = await create_access_token(db_user.email, db_user.id)
    refresh_token = await create_refresh_token(db_user.email, db_user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }

# User Login Route
@router.post("/token", status_code=status.HTTP_200_OK)
async def login(user: UserLogin, db: Session = Depends(get_db)) -> Dict:
    db_user = await authenticate(db, user.identifier, user.password)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = await create_access_token(db_user.email, db_user.id)
    refresh_token = await create_refresh_token(db_user.email, db_user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }

# Google Login Route
@router.post("/token/google", status_code=status.HTTP_200_OK)
async def login_with_google(user: UserLoginGoogle, db: Session = Depends(get_db)) -> Dict:
    db_user = await google_auth(user.google_id, db)
    access_token = await create_access_token(db_user.email, db_user.id)
    refresh_token = await create_refresh_token(db_user.email, db_user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }

@router.post("/token/facebook", status_code=status.HTTP_200_OK)
async def login_with_facebook(user: UserLoginFacebook, db: Session = Depends(get_db)) -> Dict:
    db_user = await facebook_auth(user.facebook_id, db)
    access_token = await create_access_token(db_user.email, db_user.id)
    refresh_token = await create_refresh_token(db_user.email, db_user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }


# Token Refresh Route
@router.post("/token/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(refresh_token: str = Body(...)) -> Dict:
    access_token = await refresh_access_token(refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

# User Profile Route
@router.get("/profile", status_code=status.HTTP_200_OK)
async def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict:
    db_user = await get_current_user(db, token)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "profile_picture_url": db_user.profile_picture_url,
        "latitude": db_user.latitude,
        "longitude": db_user.longitude,
        "role": db_user.role.value,
        "created_dt": db_user.created_dt,
    }

# Update User Profile Route
@router.put("/update-profile", status_code=status.HTTP_200_OK)
async def update_user_route(user_update: UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict:
    db_user = await get_current_user(db, token)
    await update_user(db, db_user, user_update)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "profile_picture_url": db_user.profile_picture_url,
        "latitude": db_user.latitude,
        "longitude": db_user.longitude,
        "role": db_user.role.value,
        "created_dt": db_user.created_dt,
    }


# Upload Profile Picture Route
@router.post("/upload-profile-picture", status_code=status.HTTP_200_OK)
async def upload_profile_picture_route(token: str = Depends(oauth2_scheme), file: UploadFile = File(...), db: Session = Depends(get_db)) -> Dict:
    db_user = await get_current_user(db, token)
    
    # Upload the profile picture and get the public URL
    profile_picture_url = await upload_profile_picture(db_user, file)
    
    # Update the user's profile picture URL in the database
    db_user.profile_picture_url = profile_picture_url
    db.commit()
    db.refresh(db_user)
    
    # Return the new profile picture URL
    return {"profile_picture_url": profile_picture_url}



# Get All Users Route
@router.get("/all-users", status_code=status.HTTP_200_OK)
async def get_all_users_route(db: Session = Depends(get_db)) -> List[Dict]:
    users = await get_all_users(db)
    return [{
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_picture_url": user.profile_picture_url,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "role": user.role.value,
        "created_dt": user.created_dt,
        "is_super_admin": user.is_super_admin,
    } for user in users]

# Admin Management Routes

# Admin Creation Route (Super Admin Only)
@router.post("/admin/create", status_code=status.HTTP_201_CREATED)
async def create_admin(user: UserCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can create an admin")
    
    db_user = await create_new_user(db, user, role=UserRole.admin)
    return {"detail": f"Admin {db_user.username} created successfully"}

# Admin Deletion Route
@router.delete("/admin/delete/{admin_id}", status_code=status.HTTP_200_OK)
async def delete_admin(admin_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can delete an admin")
    
    admin_to_delete = db.query(User).filter(User.id == admin_id, User.role == UserRole.admin).first()
    if not admin_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    
    db.delete(admin_to_delete)
    db.commit()
    return {"detail": f"Admin {admin_to_delete.username} deleted successfully"}

# List All Admins Route
@router.get("/admin/list", status_code=status.HTTP_200_OK)
async def list_admins(db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can view the list of admins")
    
    admins = db.query(User).filter(User.role == UserRole.admin).all()
    return {"admins": [{"id": admin.id, "username": admin.username, "email": admin.email} for admin in admins]}

# Setup Super Admin Route (This should be used once to create the first super admin)
@router.post("/admin/setup-super-admin", status_code=status.HTTP_201_CREATED)
async def setup_super_admin(user: UserCreate, db: Session = Depends(get_db)) -> Dict:
    db_user = await create_new_user(db, user, role=UserRole.admin, is_super_admin=True)
    return {"detail": f"Super admin {db_user.username} created successfully"}
