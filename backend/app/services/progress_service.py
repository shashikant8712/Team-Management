from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.task import Task

def recalculate_project_progress(db: Session, project_id: UUID) -> Optional[Project]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # Count total and completed tasks
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    if total_tasks == 0:
        new_progress = 0
    else:
        new_progress = int(round((completed_tasks / total_tasks) * 100))

    new_progress = max(0, min(100, new_progress))

    if project.status == "COMPLETED":
        project.progress = 100
    else:
        project.progress = new_progress

    db.commit()
    db.refresh(project)
    return project

def mark_project_completed(db: Session, project: Project) -> Project:
    project.status = "COMPLETED"
    project.progress = 100
    project.completion_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project

def mark_project_archived(db: Session, project: Project) -> Project:
    project.status = "ARCHIVED"
    project.archive_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project
