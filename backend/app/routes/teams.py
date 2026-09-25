from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.department import Department
from app.models.team import Team, TeamMember
from app.models.user import User
from app.models.role import Role
from app.schemas.team import TeamCreate, TeamUpdate, TeamOut, TeamMemberAdd, TeamMemberOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("/", response_model=List[TeamOut])
def list_teams(
    department_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("team.view")),
    db: Session = Depends(get_db)
):
    query = db.query(Team).filter(Team.organization_id == membership.organization_id)
    if department_id:
        query = query.filter(Team.department_id == department_id)
    if search:
        query = query.filter(Team.name.ilike(f"%{search}%"))

    teams = query.order_by(Team.name.asc()).all()

    results = []
    for team in teams:
        dept = db.query(Department).filter(Department.id == team.department_id).first()
        leader = db.query(User).filter(User.id == team.team_leader_id).first() if team.team_leader_id else None
        m_cnt = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.status == "ACTIVE").count()

        out = TeamOut.model_validate(team)
        out.department_name = dept.name if dept else None
        out.leader_name = leader.name if leader else None
        out.members_count = m_cnt
        results.append(out)

    return results

@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    membership: OrganizationMember = Depends(require_permission("team.create")),
    db: Session = Depends(get_db)
):
    # Verify department belongs to active organization
    dept = db.query(Department).filter(
        Department.id == data.department_id,
        Department.organization_id == membership.organization_id
    ).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Invalid department for this organization")

    # Check duplicate team name in same department
    existing = db.query(Team).filter(
        Team.organization_id == membership.organization_id,
        Team.department_id == data.department_id,
        Team.name.ilike(data.name.strip())
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Team with this name already exists in the department")

    # Verify team leader belongs to active organization
    if data.team_leader_id:
        leader_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.user_id == data.team_leader_id
        ).first()
        if not leader_mem:
            raise HTTPException(status_code=400, detail="Selected team leader is not in this organization")

    team = Team(
        organization_id=membership.organization_id,
        department_id=data.department_id,
        name=data.name.strip(),
        description=data.description,
        team_leader_id=data.team_leader_id,
        status="ACTIVE"
    )
    db.add(team)
    db.flush()

    # If leader assigned, ensure leader is also in team_members
    if data.team_leader_id:
        tm = TeamMember(team_id=team.id, user_id=data.team_leader_id, status="ACTIVE")
        db.add(tm)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="team.create",
        entity_type="team",
        entity_id=team.id,
        description=f"Created team '{team.name}' in department '{dept.name}'"
    )

    db.commit()
    db.refresh(team)

    leader = db.query(User).filter(User.id == team.team_leader_id).first() if team.team_leader_id else None
    out = TeamOut.model_validate(team)
    out.department_name = dept.name
    out.leader_name = leader.name if leader else None
    out.members_count = 1 if data.team_leader_id else 0
    return out

@router.get("/{id}", response_model=TeamOut)
def get_team(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("team.view")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    dept = db.query(Department).filter(Department.id == team.department_id).first()
    leader = db.query(User).filter(User.id == team.team_leader_id).first() if team.team_leader_id else None
    m_cnt = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.status == "ACTIVE").count()

    out = TeamOut.model_validate(team)
    out.department_name = dept.name if dept else None
    out.leader_name = leader.name if leader else None
    out.members_count = m_cnt
    return out

@router.put("/{id}", response_model=TeamOut)
def update_team(
    id: UUID,
    data: TeamUpdate,
    membership: OrganizationMember = Depends(require_permission("team.edit")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if data.department_id is not None:
        dept = db.query(Department).filter(
            Department.id == data.department_id,
            Department.organization_id == membership.organization_id
        ).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Invalid department")
        team.department_id = data.department_id

    if data.name is not None and data.name.strip() != team.name:
        existing = db.query(Team).filter(
            Team.organization_id == membership.organization_id,
            Team.department_id == team.department_id,
            Team.name.ilike(data.name.strip()),
            Team.id != id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Team name already in use in this department")
        team.name = data.name.strip()

    if data.description is not None:
        team.description = data.description

    if data.team_leader_id is not None:
        if data.team_leader_id:
            leader_mem = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == membership.organization_id,
                OrganizationMember.user_id == data.team_leader_id
            ).first()
            if not leader_mem:
                raise HTTPException(status_code=400, detail="Selected team leader not in organization")
            # Ensure leader in team_members
            tm = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.user_id == data.team_leader_id).first()
            if not tm:
                db.add(TeamMember(team_id=team.id, user_id=data.team_leader_id, status="ACTIVE"))
        team.team_leader_id = data.team_leader_id

    if data.status is not None and data.status in ["ACTIVE", "INACTIVE"]:
        team.status = data.status

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="team.edit",
        entity_type="team",
        entity_id=team.id,
        description=f"Updated team '{team.name}'"
    )

    db.commit()
    db.refresh(team)

    dept = db.query(Department).filter(Department.id == team.department_id).first()
    leader = db.query(User).filter(User.id == team.team_leader_id).first() if team.team_leader_id else None
    m_cnt = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.status == "ACTIVE").count()

    out = TeamOut.model_validate(team)
    out.department_name = dept.name if dept else None
    out.leader_name = leader.name if leader else None
    out.members_count = m_cnt
    return out

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("team.delete")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team_name = team.name
    db.delete(team)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="team.delete",
        entity_type="team",
        entity_id=id,
        description=f"Deleted team '{team_name}'"
    )

    db.commit()
    return None

@router.get("/{id}/members", response_model=List[TeamMemberOut])
def get_team_members(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("team.view")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    team_members = db.query(TeamMember).filter(TeamMember.team_id == id).all()
    results = []
    for tm in team_members:
        u = db.query(User).filter(User.id == tm.user_id).first()
        org_mem = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.user_id == tm.user_id
        ).first()
        r_name = None
        if org_mem:
            r = db.query(Role).filter(Role.id == org_mem.role_id).first()
            r_name = r.name if r else None

        results.append(TeamMemberOut(
            id=tm.id,
            team_id=tm.team_id,
            user_id=tm.user_id,
            user_name=u.name if u else "Unknown",
            user_email=u.email if u else "",
            user_role=r_name,
            joined_at=tm.joined_at,
            status=tm.status
        ))
    return results

@router.post("/{id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def add_team_member(
    id: UUID,
    data: TeamMemberAdd,
    membership: OrganizationMember = Depends(require_permission("team.assign")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Member must belong to same organization
    org_mem = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == membership.organization_id,
        OrganizationMember.user_id == data.user_id,
        OrganizationMember.status == "ACTIVE"
    ).first()
    if not org_mem:
        raise HTTPException(status_code=400, detail="User is not an active member of this organization")

    # Check duplicate team membership
    existing_tm = db.query(TeamMember).filter(
        TeamMember.team_id == id,
        TeamMember.user_id == data.user_id
    ).first()
    if existing_tm:
        if existing_tm.status != "ACTIVE":
            existing_tm.status = "ACTIVE"
            db.commit()
            db.refresh(existing_tm)
            u = db.query(User).filter(User.id == data.user_id).first()
            return TeamMemberOut(
                id=existing_tm.id,
                team_id=id,
                user_id=data.user_id,
                user_name=u.name,
                user_email=u.email,
                joined_at=existing_tm.joined_at,
                status=existing_tm.status
            )
        raise HTTPException(status_code=400, detail="User is already a member of this team")

    tm = TeamMember(team_id=id, user_id=data.user_id, status="ACTIVE")
    db.add(tm)

    u = db.query(User).filter(User.id == data.user_id).first()
    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="team.member_added",
        entity_type="team",
        entity_id=id,
        description=f"Added member '{u.name}' to team '{team.name}'"
    )

    db.commit()
    db.refresh(tm)

    return TeamMemberOut(
        id=tm.id,
        team_id=id,
        user_id=data.user_id,
        user_name=u.name,
        user_email=u.email,
        joined_at=tm.joined_at,
        status=tm.status
    )

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    id: UUID,
    user_id: UUID,
    membership: OrganizationMember = Depends(require_permission("team.assign")),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(
        Team.id == id,
        Team.organization_id == membership.organization_id
    ).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    tm = db.query(TeamMember).filter(TeamMember.team_id == id, TeamMember.user_id == user_id).first()
    if not tm:
        raise HTTPException(status_code=404, detail="User is not a member of this team")

    u = db.query(User).filter(User.id == user_id).first()
    db.delete(tm)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="team.member_removed",
        entity_type="team",
        entity_id=id,
        description=f"Removed member '{u.name if u else user_id}' from team '{team.name}'"
    )

    db.commit()
    return None
