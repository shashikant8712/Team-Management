from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    organization_name: str = Field(..., min_length=2, max_length=255)
    organization_type: str = Field(default="COMPANY")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"
    organization: Optional["OrgBrief"] = None
    role: Optional[str] = None
    permissions: List[str] = []

class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    profile_photo: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class OrgBrief(BaseModel):
    id: UUID
    name: str
    organization_type: str
    role: str

class ActiveOrgSwitch(BaseModel):
    organization_id: UUID

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

Token.model_rebuild()
