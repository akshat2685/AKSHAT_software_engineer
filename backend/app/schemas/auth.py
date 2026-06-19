"""
Pydantic schemas for authentication and user management.
"""

from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int

class UserResponse(BaseModel):
    id: str
    email: str
    name: str

    class Config:
        from_attributes = True
