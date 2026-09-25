from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.department import Department
from app.models.team import Team, TeamMember
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.activity import ActivityLog
from app.models.user import User
from app.models.role import Role
from app.schemas.dashboard import DashboardResponse, DashboardCounts, ProjectSummary, TaskSummary, ActivitySummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    membership: OrganizationMember = Depends(require_permission("dashboard.view")),
    db: Session = Depends(get_db)
):
    org_id = membership.organization_id
    role = db.query(Role).filter(Role.id == membership.role_id).first()
    role_name = role.name if role else "TEAM_MEMBER"

    # User's Department and Team information
    dept_name = None
    if membership.department_id:
        d = db.query(Department).filter(Department.id == membership.department_id).first()
        dept_name = d.name if d else None

    # Check user's team membership
    tm = db.query(TeamMember).filter(TeamMember.user_id == membership.user_id, TeamMember.status == "ACTIVE").first()
    team_name = None
    if tm:
        t = db.query(Team).filter(Team.id == tm.team_id).first()
        team_name = t.name if t else None

    # 1. Database Counts
    dept_count = db.query(Department).filter(Department.organization_id == org_id, Department.status == "ACTIVE").count()
    team_count = db.query(Team).filter(Team.organization_id == org_id, Team.status == "ACTIVE").count()
    member_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == org_id, OrganizationMember.status == "ACTIVE").count()
    active_projects_count = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.status.in_(["PLANNING", "NOT_STARTED", "IN_PROGRESS", "ON_HOLD"])
    ).count()
    pending_tasks_count = db.query(Task).filter(
        Task.organization_id == org_id,
        Task.status.in_(["TODO", "IN_PROGRESS", "REVIEW"])
    ).count()

    counts = DashboardCounts(
        departments_count=dept_count,
        teams_count=team_count,
        members_count=member_count,
        active_projects_count=active_projects_count,
        pending_tasks_count=pending_tasks_count
    )

    # 2. Current Projects (active, top 6)
    proj_query = db.query(Project).filter(
        Project.organization_id == org_id,
        Project.status.in_(["PLANNING", "NOT_STARTED", "IN_PROGRESS", "ON_HOLD"])
    )
    if role_name == "DEPARTMENT_HEAD" and membership.department_id:
        proj_query = proj_query.filter(Project.department_id == membership.department_id)
    elif role_name == "TEAM_LEADER" and tm:
        proj_query = proj_query.filter(Project.team_id == tm.team_id)
    elif role_name == "TEAM_MEMBER":
        proj_query = proj_query.join(
            ProjectMember, ProjectMember.project_id == Project.id
        ).filter(ProjectMember.user_id == membership.user_id)

    projects = proj_query.order_by(Project.created_at.desc()).limit(6).all()

    current_projects = []
    for p in projects:
        mgr = db.query(User).filter(User.id == p.project_manager_id).first() if p.project_manager_id else None
        tm_obj = db.query(Team).filter(Team.id == p.team_id).first() if p.team_id else None
        current_projects.append(ProjectSummary(
            id=p.id,
            name=p.name,
            status=p.status,
            priority=p.priority,
            progress=p.progress,
            deadline=p.deadline,
            manager_name=mgr.name if mgr else None,
            team_name=tm_obj.name if tm_obj else None
        ))

    # 3. Upcoming Tasks
    task_query = db.query(Task).filter(
        Task.organization_id == org_id,
        Task.status.in_(["TODO", "IN_PROGRESS", "REVIEW"])
    )
    if role_name == "TEAM_MEMBER":
        task_query = task_query.filter(Task.assigned_to == membership.user_id)
    elif role_name == "TEAM_LEADER" and tm:
        task_query = task_query.filter((Task.team_id == tm.team_id) | (Task.assigned_to == membership.user_id))
    elif role_name == "DEPARTMENT_HEAD" and membership.department_id:
        dept_teams = db.query(Team.id).filter(Team.department_id == membership.department_id).all()
        dept_team_ids = [t_id[0] for t_id in dept_teams]
        task_query = task_query.filter(Task.team_id.in_(dept_team_ids))

    tasks = task_query.order_by(Task.due_date.asc().nulls_last(), Task.created_at.desc()).limit(8).all()

    upcoming_tasks = []
    for t in tasks:
        p = db.query(Project).filter(Project.id == t.project_id).first()
        assignee = db.query(User).filter(User.id == t.assigned_to).first() if t.assigned_to else None
        upcoming_tasks.append(TaskSummary(
            id=t.id,
            title=t.title,
            project_name=p.name if p else None,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            assignee_name=assignee.name if assignee else None
        ))

    # 4. Recent Activity
    activities = db.query(ActivityLog).filter(
        ActivityLog.organization_id == org_id
    ).order_by(ActivityLog.created_at.desc()).limit(10).all()

    recent_activity = []
    for act in activities:
        act_user = db.query(User).filter(User.id == act.user_id).first() if act.user_id else None
        recent_activity.append(ActivitySummary(
            id=act.id,
            action=act.action,
            entity_type=act.entity_type,
            description=act.description,
            created_at=act.created_at,
            user_name=act_user.name if act_user else "System"
        ))

    return DashboardResponse(
        counts=counts,
        current_projects=current_projects,
        upcoming_tasks=upcoming_tasks,
        recent_activity=recent_activity,
        user_role=role_name,
        department_name=dept_name,
        team_name=team_name
    )
