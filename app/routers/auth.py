from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.auth import authenticate_admin, create_access_token, get_current_admin, create_default_admin
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=schemas.Token)
def login(admin_login: schemas.AdminLogin, db: Session = Depends(get_db)):
    """Authenticate admin and return JWT token."""
    admin = authenticate_admin(db, admin_login.email, admin_login.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=schemas.AdminResponse)
def get_current_admin_info(current_admin: models.Admin = Depends(get_current_admin)):
    """Get current admin information."""
    return current_admin

@router.post("/logout")
def logout(current_admin: models.Admin = Depends(get_current_admin)):
    """Logout admin (client should discard token)."""
    return {"message": "Successfully logged out"}

@router.post("/init-admin")
def init_admin(db: Session = Depends(get_db)):
    """Initialize default admin user (for setup)."""
    admin = create_default_admin(db)
    return {
        "message": "Default admin created",
        "email": admin.email,
        "note": "Change the default password in production"
    }
