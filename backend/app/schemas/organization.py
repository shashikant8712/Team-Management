from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    organization_type: str = Field(default="COMPANY")
    description: Optional[str] = None
    timezone: Optional[str] = "UTC"

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    organization_type: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None
    timezone: Optional[str] = None

class OrganizationOut(BaseModel):
    id: UUID
    name: str
    organization_type: str
    description: Optional[str] = None
    logo: Optional[str] = None
    timezone: Optional[str] = "UTC"
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
