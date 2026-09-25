from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.department import Department
from app.models.team import Team, TeamMember
from app.models.user import User
from app.models.role import Role
from app.schemas.member import MemberCreate, MemberUpdate, MemberOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/members", tags=["Members"])

@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).order_by(Role.name.asc()).all()
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]

@router.get("/", response_model=List[MemberOut])
def list_members(
    department_id: Optional[UUID] = Query(None),
    role_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("member.view")),
    db: Session = Depends(get_db)
):
    query = db.query(OrganizationMember).join(
        User, OrganizationMember.user_id == User.id
    ).join(
        Role, OrganizationMember.role_id == Role.id
    ).filter(
        OrganizationMember.organization_id == membership.organization_id
    )

    if department_id:
        query = query.filter(OrganizationMember.department_id == department_id)
    if role_name:
        query = query.filter(Role.name == role_name.upper())
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    members = query.order_by(User.name.asc()).all()

    results = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        r = db.query(Role).filter(Role.id == m.role_id).first()
        dept = db.query(Department).filter(Department.id == m.department_id).first() if m.department_id else None

        results.append(MemberOut(
            id=m.id,
            user_id=m.user_id,
            organization_id=m.organization_id,
            name=u.name,
            email=u.email,
            phone=u.phone,
            profile_photo=u.profile_photo,
            role_id=m.role_id,
            role_name=r.name if r else "TEAM_MEMBER",
            department_id=m.department_id,
            department_name=dept.name if dept else None,
            status=m.status,
            joining_date=m.joining_date,
            created_at=m.created_at
        ))

    return results

@router.post("/", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    data: MemberCreate,
    membership: OrganizationMember = Depends(require_permission("member.create")),
    db: Session = Depends(get_db)
):
    # Verify role exists
    role = db.query(Role).filter(Role.name == data.role_name.upper()).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Invalid role '{data.role_name}'")

    # Verify department if specified
    if data.department_id:
        dept = db.query(Department).filter(
            Department.id == data.department_id,
            Department.organization_id == membership.organization_id
        ).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department for this organization")

    # Find or create user
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user:
        user = User(
            name=data.name.strip(),
            email=data.email.lower(),
            password_hash=hash_password(data.password or "Member@123456"),
            phone=data.phone,
            status="ACTIVE"
        )
        db.add(user)
        db.flush()

    # Check if already a member of active organization
    existing_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == membership.organization_id,
        OrganizationMember.user_id == user.id
    ).first()

    if existing_mem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization",
        )

    new_mem = OrganizationMember(
        organization_id=membership.organization_id,
        user_id=user.id,
        role_id=role.id,
        department_id=data.department_id,
        status="ACTIVE"
    )
    db.add(new_mem)
    db.flush()

    # If team_id specified, add to team
    if data.team_id:
        team = db.query(Team).filter(
            Team.id == data.team_id,
            Team.organization_id == membership.organization_id
        ).first()
        if team:
            tm = TeamMember(team_id=team.id, user_id=user.id, status="ACTIVE")
            db.add(tm)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="member.create",
        entity_type="member",
        entity_id=user.id,
        description=f"Added member '{user.name}' ({user.email}) as {role.name}"
    )

    db.commit()
    db.refresh(new_mem)

    dept = db.query(Department).filter(Department.id == new_mem.department_id).first() if new_mem.department_id else None

    return MemberOut(
        id=new_mem.id,
        user_id=user.id,
        organization_id=new_mem.organization_id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        profile_photo=user.profile_photo,
        role_id=new_mem.role_id,
        role_name=role.name,
        department_id=new_mem.department_id,
        department_name=dept.name if dept else None,
        status=new_mem.status,
        joining_date=new_mem.joining_date,
        created_at=new_mem.created_at
    )

@router.get("/{id}", response_model=MemberOut)
def get_member(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("member.view")),
    db: Session = Depends(get_db)
):
    mem = db.query(OrganizationMember).filter(
        OrganizationMember.id == id,
        OrganizationMember.organization_id == membership.organization_id
    ).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Member not found")

    u = db.query(User).filter(User.id == mem.user_id).first()
    r = db.query(Role).filter(Role.id == mem.role_id).first()
    dept = db.query(Department).filter(Department.id == mem.department_id).first() if mem.department_id else None

    return MemberOut(
        id=mem.id,
        user_id=mem.user_id,
        organization_id=mem.organization_id,
        name=u.name,
        email=u.email,
        phone=u.phone,
        profile_photo=u.profile_photo,
        role_id=mem.role_id,
        role_name=r.name if r else "TEAM_MEMBER",
        department_id=mem.department_id,
        department_name=dept.name if dept else None,
        status=mem.status,
        joining_date=mem.joining_date,
        created_at=mem.created_at
    )

@router.put("/{id}", response_model=MemberOut)
def update_member(
    id: UUID,
    data: MemberUpdate,
    membership: OrganizationMember = Depends(require_permission("member.edit")),
    db: Session = Depends(get_db)
):
    mem = db.query(OrganizationMember).filter(
        OrganizationMember.id == id,
        OrganizationMember.organization_id == membership.organization_id
    ).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Member not found")

    if data.role_name is not None:
        role = db.query(Role).filter(Role.name == data.role_name.upper()).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Invalid role '{data.role_name}'")
        mem.role_id = role.id

    if data.department_id is not None:
        if data.department_id:
            dept = db.query(Department).filter(
                Department.id == data.department_id,
                Department.organization_id == membership.organization_id
            ).first()
            if not dept:
                raise HTTPException(status_code=400, detail="Invalid department")
        mem.department_id = data.department_id

    if data.status is not None and data.status in ["ACTIVE", "INACTIVE"]:
        mem.status = data.status

    u = db.query(User).filter(User.id == mem.user_id).first()
    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="member.edit",
        entity_type="member",
        entity_id=mem.user_id,
        description=f"Updated member record for '{u.name}'"
    )

    db.commit()
    db.refresh(mem)

    r = db.query(Role).filter(Role.id == mem.role_id).first()
    dept = db.query(Department).filter(Department.id == mem.department_id).first() if mem.department_id else None

    return MemberOut(
        id=mem.id,
        user_id=mem.user_id,
        organization_id=mem.organization_id,
        name=u.name,
        email=u.email,
        phone=u.phone,
        profile_photo=u.profile_photo,
        role_id=mem.role_id,
        role_name=r.name if r else "TEAM_MEMBER",
        department_id=mem.department_id,
        department_name=dept.name if dept else None,
        status=mem.status,
        joining_date=mem.joining_date,
        created_at=mem.created_at
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_member(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("member.delete")),
    db: Session = Depends(get_db)
):
    mem = db.query(OrganizationMember).filter(
        OrganizationMember.id == id,
        OrganizationMember.organization_id == membership.organization_id
    ).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Member not found")

    mem.status = "INACTIVE"
    u = db.query(User).filter(User.id == mem.user_id).first()

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="member.delete",
        entity_type="member",
        entity_id=mem.user_id,
        description=f"Deactivated member '{u.name if u else id}'"
    )

    db.commit()
    return None
