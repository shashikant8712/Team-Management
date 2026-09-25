from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.department import Department
from app.models.team import Team
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberAdd, ProjectMemberOut
from app.services.activity_service import log_activity
from app.services.progress_service import recalculate_project_progress, mark_project_completed, mark_project_archived

router = APIRouter(prefix="/projects", tags=["Projects"])

def enrich_project_out(db: Session, project: Project) -> ProjectOut:
    dept = db.query(Department).filter(Department.id == project.department_id).first() if project.department_id else None
    team = db.query(Team).filter(Team.id == project.team_id).first() if project.team_id else None
    manager = db.query(User).filter(User.id == project.project_manager_id).first() if project.project_manager_id else None
    creator = db.query(User).filter(User.id == project.created_by).first() if project.created_by else None

    tot_tasks = db.query(Task).filter(Task.project_id == project.id).count()
    comp_tasks = db.query(Task).filter(Task.project_id == project.id, Task.status == "COMPLETED").count()
    mem_cnt = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.status == "ACTIVE").count()

    out = ProjectOut.model_validate(project)
    out.department_name = dept.name if dept else None
    out.team_name = team.name if team else None
    out.manager_name = manager.name if manager else None
    out.creator_name = creator.name if creator else None
    out.total_tasks = tot_tasks
    out.completed_tasks = comp_tasks
    out.members_count = mem_cnt
    return out

@router.get("/", response_model=List[ProjectOut])
def list_projects(
    is_history: Optional[bool] = Query(False),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    team_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("project.view")),
    db: Session = Depends(get_db)
):
    query = db.query(Project).filter(Project.organization_id == membership.organization_id)

    if is_history:
        query = query.filter(Project.status.in_(["COMPLETED", "ARCHIVED"]))
    else:
        query = query.filter(Project.status.in_(["PLANNING", "NOT_STARTED", "IN_PROGRESS", "ON_HOLD"]))

    if status_filter:
        query = query.filter(Project.status == status_filter.upper())
    if priority:
        query = query.filter(Project.priority == priority.upper())
    if department_id:
        query = query.filter(Project.department_id == department_id)
    if team_id:
        query = query.filter(Project.team_id == team_id)
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    projects = query.order_by(Project.created_at.desc()).all()
    return [enrich_project_out(db, p) for p in projects]

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    membership: OrganizationMember = Depends(require_permission("project.create")),
    db: Session = Depends(get_db)
):
    # Validate department if provided
    if data.department_id:
        dept = db.query(Department).filter(
            Department.id == data.department_id,
            Department.organization_id == membership.organization_id
        ).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department")

    # Validate team if provided
    if data.team_id:
        team = db.query(Team).filter(
            Team.id == data.team_id,
            Team.organization_id == membership.organization_id
        ).first()
        if not team:
            raise HTTPException(status_code=400, detail="Invalid team")

    # Validate project manager if provided
    if data.project_manager_id:
        pm_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.user_id == data.project_manager_id,
            OrganizationMember.status == "ACTIVE"
        ).first()
        if not pm_mem:
            raise HTTPException(status_code=400, detail="Project manager must be an active organization member")

    valid_priorities = ["LOW", "MEDIUM", "HIGH"]
    priority = data.priority.upper() if data.priority.upper() in valid_priorities else "MEDIUM"

    valid_statuses = ["PLANNING", "NOT_STARTED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "ARCHIVED"]
    status_val = data.status.upper() if data.status.upper() in valid_statuses else "NOT_STARTED"

    project = Project(
        organization_id=membership.organization_id,
        department_id=data.department_id,
        team_id=data.team_id,
        name=data.name.strip(),
        description=data.description,
        project_manager_id=data.project_manager_id,
        start_date=data.start_date,
        deadline=data.deadline,
        priority=priority,
        status=status_val,
        progress=100 if status_val == "COMPLETED" else 0,
        completion_date=datetime.now(timezone.utc) if status_val == "COMPLETED" else None,
        created_by=membership.user_id
    )
    db.add(project)
    db.flush()

    # Add project manager to project_members automatically
    if data.project_manager_id:
        pm_link = ProjectMember(project_id=project.id, user_id=data.project_manager_id, status="ACTIVE")
        db.add(pm_link)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.create",
        entity_type="project",
        entity_id=project.id,
        description=f"Created project '{project.name}' with priority {project.priority}"
    )

    db.commit()
    db.refresh(project)

    return enrich_project_out(db, project)

@router.get("/{id}", response_model=ProjectOut)
def get_project(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.view")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return enrich_project_out(db, project)

@router.put("/{id}", response_model=ProjectOut)
def update_project(
    id: UUID,
    data: ProjectUpdate,
    membership: OrganizationMember = Depends(require_permission("project.edit")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if data.name is not None:
        project.name = data.name.strip()
    if data.description is not None:
        project.description = data.description

    if data.department_id is not None:
        if data.department_id:
            dept = db.query(Department).filter(
                Department.id == data.department_id,
                Department.organization_id == membership.organization_id
            ).first()
            if not dept:
                raise HTTPException(status_code=400, detail="Invalid department")
        project.department_id = data.department_id

    if data.team_id is not None:
        if data.team_id:
            team = db.query(Team).filter(
                Team.id == data.team_id,
                Team.organization_id == membership.organization_id
            ).first()
            if not team:
                raise HTTPException(status_code=400, detail="Invalid team")
        project.team_id = data.team_id

    if data.project_manager_id is not None:
        if data.project_manager_id:
            pm_mem = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == membership.organization_id,
                OrganizationMember.user_id == data.project_manager_id,
                OrganizationMember.status == "ACTIVE"
            ).first()
            if not pm_mem:
                raise HTTPException(status_code=400, detail="Project manager not in organization")
            # Ensure in project_members
            pm_link = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == data.project_manager_id
            ).first()
            if not pm_link:
                db.add(ProjectMember(project_id=project.id, user_id=data.project_manager_id, status="ACTIVE"))
        project.project_manager_id = data.project_manager_id

    if data.start_date is not None:
        project.start_date = data.start_date
    if data.deadline is not None:
        project.deadline = data.deadline

    if data.priority is not None:
        p_val = data.priority.upper()
        if p_val in ["LOW", "MEDIUM", "HIGH"]:
            project.priority = p_val

    if data.status is not None:
        s_val = data.status.upper()
        valid_statuses = ["PLANNING", "NOT_STARTED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "ARCHIVED"]
        if s_val in valid_statuses:
            project.status = s_val
            if s_val == "COMPLETED":
                project.progress = 100
                if not project.completion_date:
                    project.completion_date = datetime.now(timezone.utc)
            elif s_val == "ARCHIVED":
                if not project.archive_date:
                    project.archive_date = datetime.now(timezone.utc)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.edit",
        entity_type="project",
        entity_id=project.id,
        description=f"Updated project '{project.name}'"
    )

    db.commit()
    db.refresh(project)

    # Recalculate progress if not completed
    if project.status not in ["COMPLETED", "ARCHIVED"]:
        recalculate_project_progress(db, project.id)

    return enrich_project_out(db, project)

@router.post("/{id}/complete", response_model=ProjectOut)
def complete_project_endpoint(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.complete")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    mark_project_completed(db, project)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.complete",
        entity_type="project",
        entity_id=project.id,
        description=f"Completed project '{project.name}' (100% progress recorded)"
    )

    return enrich_project_out(db, project)

@router.post("/{id}/archive", response_model=ProjectOut)
def archive_project_endpoint(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.archive")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    mark_project_archived(db, project)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.archive",
        entity_type="project",
        entity_id=project.id,
        description=f"Archived project '{project.name}'"
    )

    return enrich_project_out(db, project)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.delete")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    p_name = project.name
    db.delete(project)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.delete",
        entity_type="project",
        entity_id=id,
        description=f"Deleted project '{p_name}'"
    )

    db.commit()
    return None

@router.get("/{id}/members", response_model=List[ProjectMemberOut])
def get_project_members(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.view")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pms = db.query(ProjectMember).filter(ProjectMember.project_id == id).all()
    results = []
    for pm in pms:
        u = db.query(User).filter(User.id == pm.user_id).first()
        results.append(ProjectMemberOut(
            id=pm.id,
            project_id=pm.project_id,
            user_id=pm.user_id,
            user_name=u.name if u else "Unknown",
            user_email=u.email if u else "",
            assigned_at=pm.assigned_at,
            status=pm.status
        ))
    return results

@router.post("/{id}/members", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
def add_project_member(
    id: UUID,
    data: ProjectMemberAdd,
    membership: OrganizationMember = Depends(require_permission("project.assign")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Member must belong to same organization
    org_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == membership.organization_id,
        OrganizationMember.user_id == data.user_id,
        OrganizationMember.status == "ACTIVE"
    ).first()
    if not org_mem:
        raise HTTPException(status_code=400, detail="User is not an active member of this organization")

    # Check duplicate
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == id,
        ProjectMember.user_id == data.user_id
    ).first()
    if existing:
        if existing.status != "ACTIVE":
            existing.status = "ACTIVE"
            db.commit()
            db.refresh(existing)
            u = db.query(User).filter(User.id == data.user_id).first()
            return ProjectMemberOut(
                id=existing.id,
                project_id=id,
                user_id=data.user_id,
                user_name=u.name,
                user_email=u.email,
                assigned_at=existing.assigned_at,
                status=existing.status
            )
        raise HTTPException(status_code=400, detail="User is already a member of this project")

    pm = ProjectMember(project_id=id, user_id=data.user_id, status="ACTIVE")
    db.add(pm)

    u = db.query(User).filter(User.id == data.user_id).first()
    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.assign",
        entity_type="project",
        entity_id=id,
        description=f"Assigned member '{u.name}' to project '{project.name}'"
    )

    db.commit()
    db.refresh(pm)

    return ProjectMemberOut(
        id=pm.id,
        project_id=id,
        user_id=data.user_id,
        user_name=u.name,
        user_email=u.email,
        assigned_at=pm.assigned_at,
        status=pm.status
    )

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    id: UUID,
    user_id: UUID,
    membership: OrganizationMember = Depends(require_permission("project.assign")),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == id,
        Project.organization_id == membership.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    pm = db.query(ProjectMember).filter(ProjectMember.project_id == id, ProjectMember.user_id == user_id).first()
    if not pm:
        raise HTTPException(status_code=404, detail="User is not a member of this project")

    u = db.query(User).filter(User.id == user_id).first()
    db.delete(pm)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="project.assign",
        entity_type="project",
        entity_id=id,
        description=f"Removed member '{u.name if u else user_id}' from project '{project.name}'"
    )

    db.commit()
    return None
