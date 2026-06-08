import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(80), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="idle")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="projects")
    agent_runs = relationship("AgentRun", back_populates="project", cascade="all, delete-orphan")
    test_results = relationship("TestResult", back_populates="project", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="project", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(80), ForeignKey("projects.id"), nullable=False)
    agent = Column(String(100), nullable=False)
    action = Column(Text, nullable=False)
    result = Column(Text, nullable=False)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="agent_runs")

    def set_payload(self, data):
        self.payload = json.dumps(data or {})

    def get_payload(self):
        try:
            return json.loads(self.payload)
        except Exception:
            return {}

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    outcome = Column(Text, nullable=False)
    tags = Column(String(255), default="")
    created_at = Column(DateTime, default=utc_now)

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(80), ForeignKey("projects.id"), nullable=False)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="test_results")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(80), ForeignKey("projects.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="events")

    def set_payload(self, data):
        self.payload = json.dumps(data or {})

    def get_payload(self):
        try:
            return json.loads(self.payload)
        except Exception:
            return {}
