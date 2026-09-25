from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

class MemberCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: Optional[str] = "Member@123456"
    phone: Optional[str] = None
    role_name: str = Field(default="TEAM_MEMBER")  # ADMIN, DEPARTMENT_HEAD, TEAM_LEADER, TEAM_MEMBER
    department_id: Optional[UUID] = None
    team_id: Optional[UUID] = None

class MemberUpdate(BaseModel):
    role_name: Optional[str] = None
    department_id: Optional[UUID] = None
    status: Optional[str] = None

class MemberOut(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    profile_photo: Optional[str] = None
    role_id: UUID
    role_name: str
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    status: str
    joining_date: date
    created_at: datetime

    class Config:
        from_attributes = True
