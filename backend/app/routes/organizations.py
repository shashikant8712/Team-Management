from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_current_membership, require_permission
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.role import Role
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/current", response_model=OrganizationOut)
def get_current_organization(
    membership: OrganizationMember = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.put("/current", response_model=OrganizationOut)
def update_current_organization(
    data: OrganizationUpdate,
    membership: OrganizationMember = Depends(require_permission("organization.edit")),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if data.name is not None:
        org.name = data.name
    if data.organization_type is not None:
        if data.organization_type.upper() in ["COMPANY", "COLLEGE", "OTHER"]:
            org.organization_type = data.organization_type.upper()
    if data.description is not None:
        org.description = data.description
    if data.logo is not None:
        org.logo = data.logo
    if data.timezone is not None:
        org.timezone = data.timezone

    log_activity(
        db=db,
        organization_id=org.id,
        user_id=membership.user_id,
        action="organization.edit",
        entity_type="organization",
        entity_id=org.id,
        description=f"Updated organization details: {org.name}"
    )

    db.commit()
    db.refresh(org)
    return org

@router.post("/", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    data: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
        raise HTTPException(status_code=500, detail="ADMIN role not found")

    org_type = data.organization_type.upper() if data.organization_type.upper() in ["COMPANY", "COLLEGE", "OTHER"] else "COMPANY"
    org = Organization(
        name=data.name,
        organization_type=org_type,
        description=data.description,
        timezone=data.timezone or "UTC",
        created_by=user.id,
        status="ACTIVE"
    )
    db.add(org)
    db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=admin_role.id,
        status="ACTIVE"
    )
    db.add(member)

    log_activity(
        db=db,
        organization_id=org.id,
        user_id=user.id,
        action="organization.create",
        entity_type="organization",
        entity_id=org.id,
        description=f"Created new organization: {org.name}"
    )

    db.commit()
    db.refresh(org)
    return org
