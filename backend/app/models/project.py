"""
SQLAlchemy models for project management.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base

class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"

class Project(Base):
    """Project model."""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=ProjectStatus.DRAFT)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")
    user = relationship("User", back_populates="projects")
    
    def __repr__(self):
        return f"<Project {self.id}: {self.name}>"
