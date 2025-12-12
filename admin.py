from fastapi import APIRouter, HTTPException, status
from database import db_manager
from models import AdminLogin, Token
from auth import auth_utils

router = APIRouter(prefix="/admin", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def admin_login(credentials: AdminLogin):
    """Authenticate admin and return JWT token"""
    # Find admin by email
    admin = db_manager.master_db.admins.find_one({"email": credentials.email})
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not auth_utils.verify_password(credentials.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get organization details
    organization = db_manager.master_db.organizations.find_one(
        {"admin_id": admin["_id"]}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found for this admin"
        )
    
    # Create JWT token
    token_data = {
        "admin_id": str(admin["_id"]),
        "organization_id": str(organization["_id"]),
        "email": admin["email"]
    }
    
    access_token = auth_utils.create_access_token(data=token_data)
    
    return Token(access_token=access_token, token_type="bearer")
