from typing import Optional
from pydantic import BaseModel, Field

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone: Optional[str] = None
    profile_photo: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class OrgSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    organization_type: Optional[str] = None
    description: Optional[str] = None
    timezone: Optional[str] = None
    logo: Optional[str] = None
