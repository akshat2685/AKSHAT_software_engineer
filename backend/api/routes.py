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

router = APIRouter(prefix="", tags=["auth"])

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
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already registered")
    
    hashed = hash_password(payload.password)
    user = User(email=payload.email, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token_payload = {"user_id": user.id, "email": user.email, "exp": time.time() + 86400}
    token = create_jwt_token(token_payload)
    return {"token": token, "email": user.email, "user_id": user.id}

@router.post("/auth/login")
def login(payload: AuthRequest, db: Session = Depends(get_db)):
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
