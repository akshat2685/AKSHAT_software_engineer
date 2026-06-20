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

    id = Column(String(80), primary_key=True)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    source_agent = Column(String(50), nullable=False)
    project_id = Column(String(80), nullable=True)
    task_id = Column(String(80), nullable=True)
    tags = Column(Text, default="[]")
    outcome = Column(String(50), nullable=False)
    dependencies = Column(Text, default="[]")
    confidence = Column(String(50), default="certain")
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

class ProjectMetrics(Base):
    __tablename__ = "project_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(80), ForeignKey("projects.id"), nullable=False)
    success = Column(Boolean, default=False)
    first_pass_quality = Column(Boolean, default=True)
    cost_efficiency = Column(Integer, default=100)
    user_satisfaction = Column(Integer, default=100)
    knowledge_reuse_rate = Column(Integer, default=0)
    health_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    project = relationship("Project")

class OrganizationHealth(Base):
    __tablename__ = "organization_health"
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, nullable=False)
    trend = Column(String(10), default="-")
    projects_analyzed = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

class ImprovementChangelog(Base):
    __tablename__ = "improvement_changelog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False)
    rationale = Column(Text, nullable=False)
    proposed_changes = Column(Text, nullable=False)
    status = Column(String(50), default="proposed")
    created_at = Column(DateTime, default=utc_now)

class AgentPromptOverride(Base):
    __tablename__ = "agent_prompt_override"
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_role = Column(String(100), unique=True, nullable=False)
    prompt_content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class AgentMemory(Base):
    """Production-grade agent memory (Issue 3).

    Concurrent-safe alternative to the SQLite-only ``memories`` table. On
    PostgreSQL the ``content`` column is JSONB and ``embedding`` is a
    pgvector VECTOR(1536) (see migration a1b2c3d4e5f6); on SQLite both are
    stored as TEXT/JSON so the model works in local dev too.
    """
    __tablename__ = "agent_memories"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    memory_type = Column(String(50), nullable=False)  # short_term | long_term | episodic
    content = Column(Text, nullable=False)            # JSON string (JSONB on PG)
    embedding = Column(Text, nullable=True)           # JSON list (VECTOR on PG)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
