"""
SQLAlchemy models for users.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.id}: {self.email}>"
