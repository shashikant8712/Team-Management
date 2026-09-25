from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel

class DashboardCounts(BaseModel):
    departments_count: int = 0
    teams_count: int = 0
    members_count: int = 0
    active_projects_count: int = 0
    pending_tasks_count: int = 0

class ProjectSummary(BaseModel):
    id: UUID
    name: str
    status: str
    priority: str
    progress: int
    deadline: Optional[date] = None
    manager_name: Optional[str] = None
    team_name: Optional[str] = None

class TaskSummary(BaseModel):
    id: UUID
    title: str
    project_name: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[date] = None
    assignee_name: Optional[str] = None

class ActivitySummary(BaseModel):
    id: UUID
    action: str
    entity_type: str
    description: str
    created_at: datetime
    user_name: Optional[str] = None

class DashboardResponse(BaseModel):
    counts: DashboardCounts
    current_projects: List[ProjectSummary] = []
    upcoming_tasks: List[TaskSummary] = []
    recent_activity: List[ActivitySummary] = []
    user_role: str
    department_name: Optional[str] = None
    team_name: Optional[str] = None
