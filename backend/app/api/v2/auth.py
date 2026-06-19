"""
Authentication API endpoints.
Provides registration, login, and token management.
"""

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.config import settings
from app.schemas.auth import Token, UserCreate, UserResponse
import uuid

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_tokens(user_id: str):
    # Access token
    access_payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    access_token = jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    # Refresh token
    refresh_payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS),
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    return access_token, refresh_token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if not user_id or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    # This is a placeholder. Real implementation needs DB integration.
    hashed_password = get_password_hash(user_in.password)
    user_id = str(uuid.uuid4())
    
    return UserResponse(
        id=user_id,
        email=user_in.email,
        name=user_in.name
    )

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Placeholder: Validate user in DB
    user_id = form_data.username
    access_token, refresh_token = create_tokens(user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/token/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = payload.get("sub")
        new_access_token, new_refresh_token = create_tokens(user_id)
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
