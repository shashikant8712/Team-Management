from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, hash_password
from app.dependencies.auth import get_current_user, get_current_membership, require_permission
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.schemas.auth import UserOut
from app.schemas.settings import ProfileUpdate, PasswordChangeRequest, OrgSettingsUpdate
from app.schemas.organization import OrganizationOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/profile", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user

@router.put("/profile", response_model=UserOut)
def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.name is not None:
        user.name = data.name.strip()
    if data.phone is not None:
        user.phone = data.phone.strip()
    if data.profile_photo is not None:
        user.profile_photo = data.profile_photo

    db.commit()
    db.refresh(user)
    return user

@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password does not match",
        )

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.put("/organization", response_model=OrganizationOut)
def update_org_settings(
    data: OrgSettingsUpdate,
    membership: OrganizationMember = Depends(require_permission("organization.edit")),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if data.name is not None:
        org.name = data.name.strip()
    if data.organization_type is not None:
        if data.organization_type.upper() in ["COMPANY", "COLLEGE", "OTHER"]:
            org.organization_type = data.organization_type.upper()
    if data.description is not None:
        org.description = data.description
    if data.timezone is not None:
        org.timezone = data.timezone
    if data.logo is not None:
        org.logo = data.logo

    log_activity(
        db=db,
        organization_id=org.id,
        user_id=membership.user_id,
        action="organization.edit",
        entity_type="organization",
        entity_id=org.id,
        description=f"Updated organization settings for '{org.name}'"
    )

    db.commit()
    db.refresh(org)
    return org
