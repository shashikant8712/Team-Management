from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    department_head_id: Optional[UUID] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    department_head_id: Optional[UUID] = None
    status: Optional[str] = None

class DepartmentOut(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str] = None
    department_head_id: Optional[UUID] = None
    head_name: Optional[str] = None
    status: str
    teams_count: int = 0
    members_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
