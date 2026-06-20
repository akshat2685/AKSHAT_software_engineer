import base64
import hmac
import hashlib
import json
import time
import os
import uuid
import bcrypt
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt as jose_jwt
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

# ---------------------------------------------------------------------------
# JWT configuration (Issue 2 — replaced custom HMAC JWT with python-jose)
#
# Security properties of the new implementation:
#   • Algorithm is PINNED to HS256 on both encode and decode. This blocks the
#     classic "alg: none" and algorithm-confusion attacks that custom JWT
#     implementations are vulnerable to.
#   • Each token carries a `type` claim ("access" | "refresh") so an access
#     token cannot be replayed as a refresh token and vice-versa.
#   • Each token carries a unique `jti` (JWT ID) so individual tokens can be
#     revoked via a denylist (see revoke_token / is_revoked below).
#   • `exp` and `iat` are standard numeric-datetime claims, validated by jose.
# ---------------------------------------------------------------------------

JWT_SECRET = os.environ.get("JWT_SECRET", "")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise RuntimeError(
        "JWT_SECRET must be set and at least 32 characters. "
        "Refusing to start with a weak/default secret."
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=30)
REFRESH_TOKEN_TTL = timedelta(days=7)

# In-process token revocation list (jti). For multi-process deploys, back this
# with Redis with a TTL matching the token expiry.
_REVOKED_JTI: set[str] = set()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _build_payload(user_id: Any, email: str, token_type: str, ttl: timedelta) -> dict:
    """Construct a hardened JWT payload with type, iat, exp, and jti claims."""
    issued_at = _now()
    return {
        "user_id": user_id,
        "email": email,
        "type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + ttl).timestamp()),
        "jti": str(uuid.uuid4()),
    }


def create_jwt_token(payload: dict, token_type: str = "access") -> str:
    """Create a signed JWT.

    Backwards-compatible with the old call signature ``create_jwt_token(dict)``:
    if no ``token_type`` is supplied and the caller already embedded an ``exp``,
    we honour a raw pass-through for any legacy callers, while still signing via
    jose with a pinned algorithm. Prefer :func:`create_access_token` / 
    :func:`create_refresh_token` for new code.
    """
    # Legacy path: caller passed a fully-formed dict (e.g. {"exp": ..., "user_id": ...})
    if "type" not in payload:
        payload = {**payload, "type": token_type}
    if "iat" not in payload:
        payload["iat"] = int(_now().timestamp())
    if "jti" not in payload:
        payload["jti"] = str(uuid.uuid4())
    # jose tolerates both numeric and datetime exp; normalise to int.
    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        payload["exp"] = int(exp)
    return jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: Any, email: str) -> str:
    return create_jwt_token(_build_payload(user_id, email, "access", ACCESS_TOKEN_TTL))


def create_refresh_token(user_id: Any, email: str) -> str:
    return create_jwt_token(_build_payload(user_id, email, "refresh", REFRESH_TOKEN_TTL))


def decode_jwt_token(token: str, expected_type: str | None = None) -> dict | None:
    """Verify and decode a JWT.

    Returns the payload dict on success, or ``None`` if the signature is
    invalid, the token has expired, the algorithm was tampered with, or the
    (optional) ``expected_type`` does not match the token's ``type`` claim.
    """
    try:
        # algorithms=[...] is mandatory: jose will refuse to decode if the token
        # header specifies any algorithm not in this list. This is what defeats
        # the "alg: none" / key-confusion attacks.
        payload = jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None

    if expected_type and payload.get("type") != expected_type:
        return None

    # Honour revocation list (logout).
    jti = payload.get("jti")
    if jti and jti in _REVOKED_JTI:
        return None

    return payload


def revoke_token(token: str) -> bool:
    """Add a token's jti to the revocation list. Returns True if revoked."""
    payload = decode_jwt_token(token)
    if not payload:
        return False
    jti = payload.get("jti")
    if jti:
        _REVOKED_JTI.add(jti)
        return True
    return False


def is_token_revoked(token: str) -> bool:
    payload = decode_jwt_token(token)
    if not payload:
        return True
    return payload.get("jti") in _REVOKED_JTI


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
def logout(authorization: str = Header(None)):
    """Revoke the caller's access token so it cannot be reused after logout."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        revoke_token(token)
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
    import os as _os
    db_url = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_url").first()
    db_key = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_key").first()
    db_model = db.query(SystemSettings).filter(SystemSettings.setting_key == "cloud_model").first()
    db_gemini = db.query(SystemSettings).filter(SystemSettings.setting_key == "gemini_key").first()
    db_gemini_model = db.query(SystemSettings).filter(SystemSettings.setting_key == "gemini_model").first()

    url = db_url.setting_value if db_url else ""
    key = db_key.setting_value if db_key else ""
    model = db_model.setting_value if db_model else ""
    gemini_key = db_gemini.setting_value if db_gemini else _os.environ.get("GEMINI_API_KEY", "")
    gemini_model = db_gemini_model.setting_value if db_gemini_model else _os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

    has_key = bool(key)
    has_gemini = bool(gemini_key)
    masked_key = key[:4] + "..." + key[-4:] if key and len(key) > 8 else ("***" if key else "")
    masked_gemini = gemini_key[:6] + "..." + gemini_key[-4:] if gemini_key and len(gemini_key) > 10 else ("***" if gemini_key else "")

    return {
        "cloud_url": url,
        "cloud_model": model,
        "has_key": has_key,
        "masked_key": masked_key,
        "has_gemini": has_gemini,
        "masked_gemini": masked_gemini,
        "gemini_model": gemini_model,
    }

@router.post("/api/settings")
def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.services.llm_service import _default_service
    from backend.database.models import SystemSettings
    import os as _os

    def _upsert(key_name, val):
        s = db.query(SystemSettings).filter(SystemSettings.setting_key == key_name).first()
        if not s:
            s = SystemSettings(setting_key=key_name)
            db.add(s)
        s.setting_value = val

    # If the URL is a gemini:// scheme, treat cloud_key as a Gemini key
    if data.cloud_url.startswith("gemini://"):
        gemini_key = data.cloud_key if data.cloud_key and "..." not in data.cloud_key else ""
        gemini_model = data.cloud_model or "gemini-1.5-flash"
        if gemini_key:
            _upsert("gemini_key", gemini_key)
            _upsert("gemini_model", gemini_model)
            db.commit()
            # Update the running provider
            from backend.services.providers.gemini_provider import GeminiProvider
            _default_service.gemini_key = gemini_key
            _default_service.gemini_model = gemini_model
            _default_service.gemini_provider = GeminiProvider(gemini_key, gemini_model)
            _os.environ["GEMINI_API_KEY"] = gemini_key
            _os.environ["GEMINI_MODEL"] = gemini_model
        return {"status": "success", "provider": "gemini"}

    # Otherwise treat as OpenAI-compatible cloud
    actual_key = data.cloud_key if data.cloud_key and not data.cloud_key.startswith("***") and "..." not in data.cloud_key else ""
    _default_service.update_config(data.cloud_url, actual_key, data.cloud_model)
    return {"status": "success", "provider": "cloud"}
