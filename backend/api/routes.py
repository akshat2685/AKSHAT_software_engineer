import base64
import hmac
import hashlib
import json
import time
import os
import bcrypt
from typing import Dict, Any, List
from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import User, Project, Event
from supabase import create_client, Client

router = APIRouter(prefix="", tags=["auth"])

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

def get_supabase() -> Client | None:
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

JWT_SECRET = os.environ.get("JWT_SECRET", "akshat_v2_super_secret_key_123456")
JWT_ALGORITHM = "HS256"

# JWT Utilities
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt_token(payload: dict) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    unsigned_token = base64url_encode(header_json) + "." + base64url_encode(payload_json)
    signature = hmac.new(JWT_SECRET.encode('utf-8'), unsigned_token.encode('utf-8'), hashlib.sha256).digest()
    return unsigned_token + "." + base64url_encode(signature)

def decode_jwt_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        unsigned_token = parts[0] + "." + parts[1]
        signature = base64url_decode(parts[2])
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), unsigned_token.encode('utf-8'), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload_data = json.loads(base64url_decode(parts[1]).decode('utf-8'))
        if "exp" in payload_data and payload_data["exp"] < time.time():
            return None
        return payload_data
    except Exception:
        return None

# Password Utilities
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

# Pydantic Schemas
class AuthRequest(BaseModel):
    email: str
    password: str

# Dependency to check auth
def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: missing token")
    token = authorization.split(" ")[1]
    payload = decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or expired token")
    return payload

@router.post("/auth/register")
def register(payload: AuthRequest, db: Session = Depends(get_db)):
    supabase = get_supabase()
    
    if supabase:
        try:
            # Register with Supabase
            res = supabase.auth.sign_up({"email": payload.email, "password": payload.password})
            if not res or not res.user:
                raise HTTPException(status_code=400, detail="Supabase registration failed")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    # Check local DB
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        if not supabase:
            raise HTTPException(status_code=400, detail="User already registered locally")
        user = existing
    else:
        # Create local user record for foreign keys
        hashed = hash_password(payload.password) if not supabase else ""
        user = User(email=payload.email, password_hash=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token_payload = {"user_id": user.id, "email": user.email, "exp": time.time() + 86400}
    token = create_jwt_token(token_payload)
    return {"token": token, "email": user.email, "user_id": user.id}

@router.post("/auth/login")
def login(payload: AuthRequest, db: Session = Depends(get_db)):
    supabase = get_supabase()
    
    if supabase:
        try:
            res = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
            if not res or not res.session:
                raise HTTPException(status_code=400, detail="Invalid Supabase credentials")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        # Ensure local user exists
        user = db.query(User).filter(User.email == payload.email).first()
        if not user:
            user = User(email=payload.email, password_hash="")
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        user = db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token_payload = {"user_id": user.id, "email": user.email, "exp": time.time() + 86400}
    token = create_jwt_token(token_payload)
    return {"token": token, "email": user.email, "user_id": user.id}

@router.post("/auth/logout")
def logout():
    return {"ok": True}

@router.get("/api/projects")
def list_projects(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("user_id")
    projects = db.query(Project).filter(Project.user_id == user_id).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "status": p.status,
            "created_at": p.created_at.isoformat()
        } for p in projects
    ]

@router.get("/api/projects/{id}/replay")
def get_replay_events(id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("user_id")
    project = db.query(Project).filter(Project.id == id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    events = db.query(Event).filter(Event.project_id == id).order_by(Event.id.asc()).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "payload": e.get_payload(),
            "created_at": e.created_at.isoformat()
        } for e in events
    ]

class SettingsUpdate(BaseModel):
    cloud_url: str = ""
    cloud_key: str = ""
    cloud_model: str = ""

@router.get("/api/settings")
def get_settings(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.database.models import SystemSettings
    db_url = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_url").first()
    db_key = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_key").first()
    db_model = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_model").first()
    
    url = db_url.setting_value if db_url else ""
    key = db_key.setting_value if db_key else ""
    model = db_model.setting_value if db_model else ""
    
    # Do not send the full key to the frontend for security, just whether it exists
    has_key = bool(key)
    masked_key = key[:4] + "..." + key[-4:] if key and len(key) > 8 else ("***" if key else "")

    return {
        "cloud_url": url,
        "cloud_model": model,
        "has_key": has_key,
        "masked_key": masked_key
    }

@router.post("/api/settings")
def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    from backend.services.llm_service import _default_service
    # If the frontend passes a dummy masked string, don't override the actual key
    actual_key = data.cloud_key if data.cloud_key and not data.cloud_key.startswith("***") and "..." not in data.cloud_key else ""
    _default_service.update_config(data.cloud_url, actual_key, data.cloud_model)
    return {"status": "success"}
