from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..config import settings
from ..db import get_db
from .. import models, schemas
from .logger import log_auth_event, log_error

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

def authenticate_admin(db: Session, email: str, password: str) -> Optional[models.Admin]:
    """Authenticate an admin user."""
    admin = db.query(models.Admin).filter(models.Admin.email == email).first()
    if not admin:
        log_auth_event("login_attempt", email=email, success=False, reason="user_not_found")
        return None
    if not verify_password(password, admin.hashed_password):
        log_auth_event("login_attempt", email=email, success=False, reason="invalid_password")
        return None
    
    log_auth_event("login_success", email=email, success=True, admin_id=admin.id)
    return admin

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.Admin:
    """Get the current authenticated admin."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        email = verify_token(token)
        if email is None:
            log_auth_event("token_validation", success=False, reason="invalid_token")
            raise credentials_exception
    except Exception as e:
        log_error(e, context={"operation": "token_validation"})
        raise credentials_exception
    
    admin = db.query(models.Admin).filter(models.Admin.email == email).first()
    if admin is None:
        log_auth_event("token_validation", email=email, success=False, reason="admin_not_found")
        raise credentials_exception
    
    if not admin.is_active:
        log_auth_event("token_validation", email=email, success=False, reason="inactive_account")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive admin account"
        )
    
    return admin

def create_default_admin(db: Session):
    """Create a default admin user if none exists."""
    existing_admin = db.query(models.Admin).first()
    if not existing_admin:
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        admin = models.Admin(
            email=settings.ADMIN_EMAIL,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    return existing_admin
