from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.project import Project
from app.models.team import Team
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskOut
from app.services.activity_service import log_activity
from app.services.progress_service import recalculate_project_progress

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def enrich_task_out(db: Session, task: Task) -> TaskOut:
    project = db.query(Project).filter(Project.id == task.project_id).first()
    team = db.query(Team).filter(Team.id == task.team_id).first() if task.team_id else None
    assignee = db.query(User).filter(User.id == task.assigned_to).first() if task.assigned_to else None

    out = TaskOut.model_validate(task)
    out.project_name = project.name if project else None
    out.team_name = team.name if team else None
    out.assignee_name = assignee.name if assignee else None
    return out

@router.get("/", response_model=List[TaskOut])
def list_tasks(
    project_id: Optional[UUID] = Query(None),
    team_id: Optional[UUID] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("task.view")),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.organization_id == membership.organization_id)

    if project_id:
        query = query.filter(Task.project_id == project_id)
    if team_id:
        query = query.filter(Task.team_id == team_id)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if status_filter:
        query = query.filter(Task.status == status_filter.upper())
    if priority:
        query = query.filter(Task.priority == priority.upper())
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    tasks = query.order_by(Task.created_at.desc()).all()
    return [enrich_task_out(db, t) for t in tasks]

@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    membership: OrganizationMember = Depends(require_permission("task.create")),
    db: Session = Depends(get_db)
):
    # Verify project belongs to organization
    project = db.query(Project).filter(
        Project.id == data.project_id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=400, detail="Invalid project for this organization")

    # Verify team if specified
    if data.team_id:
        team = db.query(Team).filter(
            Team.id == data.team_id,
            Team.organization_id == membership.organization_id
        ).first()
        if not team:
            raise HTTPException(status_code=400, detail="Invalid team")

    # Verify assignee if specified
    if data.assigned_to:
        assignee_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.user_id == data.assigned_to,
            OrganizationMember.status == "ACTIVE"
        ).first()
        if not assignee_mem:
            raise HTTPException(status_code=400, detail="Assignee is not an active organization member")

    valid_statuses = ["TODO", "IN_PROGRESS", "REVIEW", "COMPLETED"]
    t_status = data.status.upper() if data.status.upper() in valid_statuses else "TODO"

    valid_priorities = ["LOW", "MEDIUM", "HIGH", "URGENT"]
    t_priority = data.priority.upper() if data.priority.upper() in valid_priorities else "MEDIUM"

    task = Task(
        organization_id=membership.organization_id,
        project_id=data.project_id,
        team_id=data.team_id or project.team_id,
        title=data.title.strip(),
        description=data.description,
        assigned_to=data.assigned_to,
        created_by=membership.user_id,
        start_date=data.start_date,
        due_date=data.due_date,
        status=t_status,
        priority=t_priority,
        completed_at=datetime.now(timezone.utc) if t_status == "COMPLETED" else None
    )
    db.add(task)
    db.flush()

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="task.create",
        entity_type="task",
        entity_id=task.id,
        description=f"Created task '{task.title}' in project '{project.name}'"
    )

    db.commit()
    db.refresh(task)

    # Recalculate project progress
    recalculate_project_progress(db, task.project_id)

    return enrich_task_out(db, task)

@router.get("/{id}", response_model=TaskOut)
def get_task(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("task.view")),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == id,
        Task.organization_id == membership.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return enrich_task_out(db, task)

@router.put("/{id}", response_model=TaskOut)
def update_task(
    id: UUID,
    data: TaskUpdate,
    membership: OrganizationMember = Depends(require_permission("task.edit")),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == id,
        Task.organization_id == membership.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if data.title is not None:
        task.title = data.title.strip()
    if data.description is not None:
        task.description = data.description

    if data.assigned_to is not None:
        if data.assigned_to:
            assignee_mem = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == membership.organization_id,
                OrganizationMember.user_id == data.assigned_to,
                OrganizationMember.status == "ACTIVE"
            ).first()
            if not assignee_mem:
                raise HTTPException(status_code=400, detail="Assignee is not an active organization member")
        task.assigned_to = data.assigned_to

    if data.team_id is not None:
        if data.team_id:
            team = db.query(Team).filter(
                Team.id == data.team_id,
                Team.organization_id == membership.organization_id
            ).first()
            if not team:
                raise HTTPException(status_code=400, detail="Invalid team")
        task.team_id = data.team_id

    if data.start_date is not None:
        task.start_date = data.start_date
    if data.due_date is not None:
        task.due_date = data.due_date

    if data.priority is not None:
        p_val = data.priority.upper()
        if p_val in ["LOW", "MEDIUM", "HIGH", "URGENT"]:
            task.priority = p_val

    if data.status is not None:
        s_val = data.status.upper()
        if s_val in ["TODO", "IN_PROGRESS", "REVIEW", "COMPLETED"]:
            if s_val == "COMPLETED" and task.status != "COMPLETED":
                task.completed_at = datetime.now(timezone.utc)
            elif s_val != "COMPLETED" and task.status == "COMPLETED":
                task.completed_at = None
            task.status = s_val

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="task.edit",
        entity_type="task",
        entity_id=task.id,
        description=f"Updated task '{task.title}'"
    )

    db.commit()
    db.refresh(task)

    # Recalculate progress
    recalculate_project_progress(db, task.project_id)

    return enrich_task_out(db, task)

@router.patch("/{id}/status", response_model=TaskOut)
def update_task_status(
    id: UUID,
    data: TaskStatusUpdate,
    membership: OrganizationMember = Depends(require_permission("task.update_status")),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == id,
        Task.organization_id == membership.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = data.status.upper()
    valid_statuses = ["TODO", "IN_PROGRESS", "REVIEW", "COMPLETED"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    old_status = task.status
    task.status = new_status

    if new_status == "COMPLETED":
        task.completed_at = datetime.now(timezone.utc)
        action = "task.completed"
        desc = f"Completed task '{task.title}'"
    else:
        task.completed_at = None
        action = "task.reopened" if old_status == "COMPLETED" else "task.update_status"
        desc = f"Updated status of task '{task.title}' to {new_status}"

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action=action,
        entity_type="task",
        entity_id=task.id,
        description=desc
    )

    db.commit()
    db.refresh(task)

    # Recalculate project progress
    recalculate_project_progress(db, task.project_id)

    return enrich_task_out(db, task)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("task.delete")),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(
        Task.id == id,
        Task.organization_id == membership.organization_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    project_id = task.project_id
    t_title = task.title
    db.delete(task)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="task.delete",
        entity_type="task",
        entity_id=id,
        description=f"Deleted task '{t_title}'"
    )

    db.commit()

    # Recalculate progress
    recalculate_project_progress(db, project_id)

    return None
