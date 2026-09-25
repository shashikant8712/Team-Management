from datetime import datetime, timezone
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.role import Role, Permission, RolePermission
from app.schemas.auth import UserRegister, UserLogin, Token, UserOut, OrgBrief, ActiveOrgSwitch
from app.services.activity_service import log_activity

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_user_role_and_permissions(db: Session, membership: OrganizationMember):
    role = db.query(Role).filter(Role.id == membership.role_id).first()
    role_name = role.name if role else "TEAM_MEMBER"
    
    perms = db.query(Permission.code).join(
        RolePermission, RolePermission.permission_id == Permission.id
    ).filter(RolePermission.role_id == membership.role_id).all()
    
    perm_codes = [p[0] for p in perms]
    return role_name, perm_codes

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists",
        )

    # 2. Find ADMIN role
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System roles not initialized. Please run seed.py",
        )

    # 3. Create User
    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        status="ACTIVE"
    )
    db.add(user)
    db.flush()

    # 4. Create Organization
    org_type = data.organization_type.upper() if data.organization_type.upper() in ["COMPANY", "COLLEGE", "OTHER"] else "COMPANY"
    org = Organization(
        name=data.organization_name,
        organization_type=org_type,
        created_by=user.id,
        status="ACTIVE"
    )
    db.add(org)
    db.flush()

    # 5. Create Organization Member with ADMIN role
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role_id=admin_role.id,
        status="ACTIVE"
    )
    db.add(member)
    db.flush()

    # 6. Log activity
    log_activity(
        db=db,
        organization_id=org.id,
        user_id=user.id,
        action="organization.create",
        entity_type="organization",
        entity_id=org.id,
        description=f"Created organization '{org.name}' with owner {user.name}"
    )

    db.commit()
    db.refresh(user)
    db.refresh(org)

    role_name, perm_codes = get_user_role_and_permissions(db, member)

    # 7. Generate JWT token
    token_data = {
        "sub": str(user.id),
        "org_id": str(org.id),
        "role": role_name,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
        organization=OrgBrief(id=org.id, name=org.name, organization_type=org.organization_type, role=role_name),
        role=role_name,
        permissions=perm_codes
    )

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive. Please contact your administrator.",
        )

    # Find user's active organization memberships
    memberships = db.query(OrganizationMember).join(
        Organization, OrganizationMember.organization_id == Organization.id
    ).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == "ACTIVE",
        Organization.status == "ACTIVE"
    ).all()

    active_org_brief = None
    role_name = None
    perm_codes: List[str] = []

    if memberships:
        primary_membership = memberships[0]
        org = db.query(Organization).filter(Organization.id == primary_membership.organization_id).first()
        role_name, perm_codes = get_user_role_and_permissions(db, primary_membership)
        active_org_brief = OrgBrief(id=org.id, name=org.name, organization_type=org.organization_type, role=role_name)
        org_id_str = str(org.id)
    else:
        org_id_str = None

    token_data = {
        "sub": str(user.id),
        "org_id": org_id_str,
        "role": role_name,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
        organization=active_org_brief,
        role=role_name,
        permissions=perm_codes
    )

@router.get("/me", response_model=Token)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(OrganizationMember).join(
        Organization, OrganizationMember.organization_id == Organization.id
    ).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == "ACTIVE",
        Organization.status == "ACTIVE"
    ).all()

    active_org_brief = None
    role_name = None
    perm_codes: List[str] = []

    if memberships:
        primary_membership = memberships[0]
        org = db.query(Organization).filter(Organization.id == primary_membership.organization_id).first()
        role_name, perm_codes = get_user_role_and_permissions(db, primary_membership)
        active_org_brief = OrgBrief(id=org.id, name=org.name, organization_type=org.organization_type, role=role_name)
        org_id_str = str(org.id)
    else:
        org_id_str = None

    token_data = {
        "sub": str(user.id),
        "org_id": org_id_str,
        "role": role_name,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
        organization=active_org_brief,
        role=role_name,
        permissions=perm_codes
    )

@router.get("/my-organizations", response_model=List[OrgBrief])
def get_my_organizations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(OrganizationMember).join(
        Organization, OrganizationMember.organization_id == Organization.id
    ).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == "ACTIVE",
        Organization.status == "ACTIVE"
    ).all()

    result = []
    for m in memberships:
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        role = db.query(Role).filter(Role.id == m.role_id).first()
        result.append(OrgBrief(
            id=org.id,
            name=org.name,
            organization_type=org.organization_type,
            role=role.name if role else "TEAM_MEMBER"
        ))
    return result

@router.post("/switch-organization", response_model=Token)
def switch_organization(
    data: ActiveOrgSwitch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.organization_id == data.organization_id,
        OrganizationMember.status == "ACTIVE"
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an active member of this organization",
        )

    org = db.query(Organization).filter(Organization.id == data.organization_id).first()
    role_name, perm_codes = get_user_role_and_permissions(db, membership)

    token_data = {
        "sub": str(user.id),
        "org_id": str(org.id),
        "role": role_name,
    }
    access_token = create_access_token(data=token_data)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
        organization=OrgBrief(id=org.id, name=org.name, organization_type=org.organization_type, role=role_name),
        role=role_name,
        permissions=perm_codes
    )
