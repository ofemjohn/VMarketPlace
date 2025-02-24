from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import List, Dict
from src.auth.schemas import UserCreate, UserUpdate, UserLogin, ForgotPasswordRequest, ResetPasswordRequest, UserLoginGoogle
from src.database import get_db
from fastapi.security import OAuth2PasswordBearer
import os
import requests

from src.auth.services import (
    existing_user_by_email, 
    create_access_token, 
    create_refresh_token, 
    get_current_user, 
    authenticate, 
    update_user,
    refresh_access_token,
    create_user as create_new_user,
    upload_profile_picture,
    get_all_users,
    generate_reset_token,
    send_reset_email,
    reset_user_password,
    google_auth
)
from src.auth.models import User, UserRole  # Import User and UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI")

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

### **User Registration**
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_user(user: UserCreate, db: Session = Depends(get_db)) -> Dict:
    # check if i need ths line below
    if await existing_user_by_email(db, user.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    
    db_user = await create_new_user(db, user, role=UserRole.user)
    access_token = await create_access_token(db_user.email, db_user.id)
    refresh_token = await create_refresh_token(db_user.email, db_user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }

### **User Login**
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
            "full_name": db_user.full_name,
            "email": db_user.email,
            "profile_picture_url": db_user.profile_picture_url,
            "latitude": db_user.latitude,
            "longitude": db_user.longitude,
            "role": db_user.role.value,
            "created_dt": db_user.created_dt,
        }
    }

### **Token Refresh**
@router.post("/token/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(refresh_token: str = Body(...)) -> Dict:
    access_token = await refresh_access_token(refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

### **User Profile**
@router.get("/profile", status_code=status.HTTP_200_OK)
async def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict:
    db_user = await get_current_user(db, token)
    return {
        "id": db_user.id,
        "full_name": db_user.full_name,
        "email": db_user.email,
        "profile_picture_url": db_user.profile_picture_url,
        "latitude": db_user.latitude,
        "longitude": db_user.longitude,
        "role": db_user.role.value,
        "created_dt": db_user.created_dt,
    }

### **Update User Profile**
@router.put("/update-profile", status_code=status.HTTP_200_OK)
async def update_user_route(user_update: UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Dict:
    db_user = await get_current_user(db, token)
    await update_user(db, db_user, user_update)
    
    return {
        "id": db_user.id,
        "full_name": db_user.full_name,
        "email": db_user.email,
        "profile_picture_url": db_user.profile_picture_url,
        "latitude": db_user.latitude,
        "longitude": db_user.longitude,
        "role": db_user.role.value,
        "created_dt": db_user.created_dt,
    }

### **Upload Profile Picture**
@router.post("/upload-profile-picture", status_code=status.HTTP_200_OK)
async def upload_profile_picture_route(
    token: str = Depends(oauth2_scheme), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
) -> Dict:
    db_user = await get_current_user(db, token)
    profile_picture_url = await upload_profile_picture(db, db_user, file)
    return {"profile_picture_url": profile_picture_url}

### **Get All Users**
@router.get("/all-users", status_code=status.HTTP_200_OK)
async def get_all_users_route(db: Session = Depends(get_db)) -> List[Dict]:
    users = await get_all_users(db)
    return [{
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "profile_picture_url": user.profile_picture_url,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "role": user.role.value,
        "created_dt": user.created_dt,
        "is_super_admin": user.is_super_admin,
    } for user in users]

### **Admin Management**
#### **Create Admin (Super Admin Only)**
@router.post("/admin/create", status_code=status.HTTP_201_CREATED)
async def create_admin(user: UserCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can create an admin")
    
    db_user = await create_new_user(db, user, role=UserRole.admin)
    return {"detail": f"Admin {db_user.full_name} created successfully"}

#### **Delete Admin**
@router.delete("/admin/delete/{admin_id}", status_code=status.HTTP_200_OK)
async def delete_admin(admin_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can delete an admin")
    
    admin_to_delete = db.query(User).filter(User.id == admin_id, User.role == UserRole.admin).first()
    if not admin_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    
    db.delete(admin_to_delete)
    db.commit()
    return {"detail": f"Admin {admin_to_delete.full_name} deleted successfully"}

#### **List All Admins**
@router.get("/admin/list", status_code=status.HTTP_200_OK)
async def list_admins(db: Session = Depends(get_db), current_user = Depends(get_current_user)) -> Dict:
    if current_user.role != UserRole.admin or not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admin can view admins")
    
    admins = db.query(User).filter(User.role == UserRole.admin).all()
    return {"admins": [{"id": admin.id, "username": admin.full_name, "email": admin.email} for admin in admins]}

#### **Setup Super Admin**
@router.post("/admin/setup-super-admin", status_code=status.HTTP_201_CREATED)
async def setup_super_admin(user: UserCreate, db: Session = Depends(get_db)) -> Dict:
    db_user = await create_new_user(db, user, role=UserRole.admin, is_super_admin=True)
    return {"detail": f"Super admin {db_user.full_name} created successfully"}


@router.post("/forgot-password", status_code=200)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Handles forgot password request."""
    reset_token = await generate_reset_token(db, request.email)

    if not reset_token:
        raise HTTPException(status_code=404, detail="User with this email not found.")

    await send_reset_email(request.email, reset_token)
    return {"message": "Password reset email sent successfully."}



@router.post("/reset-password", status_code=200)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Handles password reset using the provided token."""
    success = await reset_user_password(db, request.token, request.new_password)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    return {"message": "Password reset successfully."}



@router.post("/google-login", status_code=200)
async def google_login(request: UserLoginGoogle, db: Session = Depends(get_db)):
    return await google_auth(db, request.id_token)  # ✅ Change google_id to id_token



@router.get("/facebook-login")
async def facebook_login():
    """Redirect user to Facebook OAuth login"""
    return {
        "login_url": f"https://www.facebook.com/v18.0/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri={FACEBOOK_REDIRECT_URI}&scope=email"
    }


@router.get("/facebook-callback")
async def facebook_callback(code: str, db: Session = Depends(get_db)):
    """Handle Facebook OAuth Callback"""
    try:
        # Exchange code for an access token
        token_url = f"https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            "client_id": FACEBOOK_CLIENT_ID,
            "client_secret": FACEBOOK_CLIENT_SECRET,
            "redirect_uri": FACEBOOK_REDIRECT_URI,
            "code": code,
        }
        response = requests.get(token_url, params=params)
        data = response.json()

        if "access_token" not in data:
            raise HTTPException(status_code=400, detail="Invalid Facebook code")

        access_token = data["access_token"]

        # Fetch User Info from Facebook API
        user_info_url = "https://graph.facebook.com/me?fields=id,name,email,picture&access_token=" + access_token
        user_response = requests.get(user_info_url)
        user_data = user_response.json()

        if "email" not in user_data:
            raise HTTPException(status_code=400, detail="Email permission not granted")

        email = user_data["email"]
        name = user_data["name"]
        profile_picture = user_data["picture"]["data"]["url"] if "picture" in user_data else None

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user
            new_user = User(
                email=email,
                full_name=name,
                profile_picture_url=profile_picture,
                facebook_id=user_data["id"],
                role=UserRole.user
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user

        # Generate JWT Tokens
        access_token = await create_access_token(user.email, user.id)
        refresh_token = await create_refresh_token(user.email, user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "profile_picture_url": user.profile_picture_url,
                "role": user.role.value,
                "created_dt": user.created_dt,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
