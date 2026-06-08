import json
from sqlalchemy.orm import Session
from backend.database.models import Project, AgentRun, TestResult, Event

def create_project(db: Session, project_id: str, name: str, user_id: int) -> Project:
    project = Project(id=project_id, name=name, user_id=user_id, status="thinking")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def update_project_status(db: Session, project_id: str, status: str):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.status = status
        db.commit()

def log_project_event(db: Session, project_id: str, event_type: str, payload: dict):
    # event_type: "PROJECT_CREATED", "AGENT_STARTED", "AGENT_COMPLETED", "FILE_CREATED", "FILE_MODIFIED", "TEST_STARTED", "TEST_COMPLETED", "PROJECT_COMPLETED"
    event = Event(project_id=project_id, event_type=event_type)
    event.set_payload(payload)
    db.add(event)
    db.commit()

def log_agent_run(db: Session, project_id: str, agent: str, action: str, result: str, payload: dict):
    run = AgentRun(project_id=project_id, agent=agent, action=action, result=result)
    run.set_payload(payload)
    db.add(run)
    db.commit()

def log_test_result(db: Session, project_id: str, passed: int, failed: int, summary: str):
    res = TestResult(project_id=project_id, passed=passed, failed=failed, summary=summary)
    db.add(res)
    db.commit()
