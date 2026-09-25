from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_membership, require_permission
from app.models.organization import OrganizationMember
from app.models.department import Department
from app.models.team import Team
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.services.activity_service import log_activity

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("/", response_model=List[DepartmentOut])
def list_departments(
    search: Optional[str] = Query(None),
    membership: OrganizationMember = Depends(require_permission("department.view")),
    db: Session = Depends(get_db)
):
    query = db.query(Department).filter(
        Department.organization_id == membership.organization_id
    )
    if search:
        query = query.filter(Department.name.ilike(f"%{search}%"))

    departments = query.order_by(Department.name.asc()).all()

    results = []
    for dept in departments:
        head_name = None
        if dept.department_head_id:
            head = db.query(User).filter(User.id == dept.department_head_id).first()
            if head:
                head_name = head.name

        teams_cnt = db.query(Team).filter(
            Team.department_id == dept.id,
            Team.organization_id == membership.organization_id
        ).count()

        members_cnt = db.query(OrganizationMember).filter(
            OrganizationMember.department_id == dept.id,
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.status == "ACTIVE"
        ).count()

        out = DepartmentOut.model_validate(dept)
        out.head_name = head_name
        out.teams_count = teams_cnt
        out.members_count = members_cnt
        results.append(out)

    return results

@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    data: DepartmentCreate,
    membership: OrganizationMember = Depends(require_permission("department.create")),
    db: Session = Depends(get_db)
):
    # Check duplicate name within this organization
    existing = db.query(Department).filter(
        Department.organization_id == membership.organization_id,
        Department.name.ilike(data.name.strip())
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with name '{data.name}' already exists in this organization",
        )

    # Validate head if provided
    if data.department_head_id:
        head_membership = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == membership.organization_id,
            OrganizationMember.user_id == data.department_head_id
        ).first()
        if not head_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected department head is not a member of this organization",
            )

    dept = Department(
        organization_id=membership.organization_id,
        name=data.name.strip(),
        description=data.description,
        department_head_id=data.department_head_id,
        status="ACTIVE"
    )
    db.add(dept)
    db.flush()

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="department.create",
        entity_type="department",
        entity_id=dept.id,
        description=f"Created department '{dept.name}'"
    )

    db.commit()
    db.refresh(dept)

    head_name = None
    if dept.department_head_id:
        head = db.query(User).filter(User.id == dept.department_head_id).first()
        head_name = head.name if head else None

    out = DepartmentOut.model_validate(dept)
    out.head_name = head_name
    return out

@router.get("/{id}", response_model=DepartmentOut)
def get_department(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("department.view")),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(
        Department.id == id,
        Department.organization_id == membership.organization_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    head_name = None
    if dept.department_head_id:
        head = db.query(User).filter(User.id == dept.department_head_id).first()
        head_name = head.name if head else None

    teams_cnt = db.query(Team).filter(Team.department_id == dept.id).count()
    members_cnt = db.query(OrganizationMember).filter(
        OrganizationMember.department_id == dept.id,
        OrganizationMember.status == "ACTIVE"
    ).count()

    out = DepartmentOut.model_validate(dept)
    out.head_name = head_name
    out.teams_count = teams_cnt
    out.members_count = members_cnt
    return out

@router.put("/{id}", response_model=DepartmentOut)
def update_department(
    id: UUID,
    data: DepartmentUpdate,
    membership: OrganizationMember = Depends(require_permission("department.edit")),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(
        Department.id == id,
        Department.organization_id == membership.organization_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    if data.name is not None and data.name.strip() != dept.name:
        existing = db.query(Department).filter(
            Department.organization_id == membership.organization_id,
            Department.name.ilike(data.name.strip()),
            Department.id != id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department with name '{data.name}' already exists in this organization",
            )
        dept.name = data.name.strip()

    if data.description is not None:
        dept.description = data.description

    if data.department_head_id is not None:
        if data.department_head_id:
            head_membership = db.query(OrganizationMember).filter(
                OrganizationMember.organization_id == membership.organization_id,
                OrganizationMember.user_id == data.department_head_id
            ).first()
            if not head_membership:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected department head is not a member of this organization",
                )
        dept.department_head_id = data.department_head_id

    if data.status is not None and data.status in ["ACTIVE", "INACTIVE"]:
        dept.status = data.status

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="department.edit",
        entity_type="department",
        entity_id=dept.id,
        description=f"Updated department '{dept.name}'"
    )

    db.commit()
    db.refresh(dept)

    head_name = None
    if dept.department_head_id:
        head = db.query(User).filter(User.id == dept.department_head_id).first()
        head_name = head.name if head else None

    teams_cnt = db.query(Team).filter(Team.department_id == dept.id).count()
    members_cnt = db.query(OrganizationMember).filter(
        OrganizationMember.department_id == dept.id,
        OrganizationMember.status == "ACTIVE"
    ).count()

    out = DepartmentOut.model_validate(dept)
    out.head_name = head_name
    out.teams_count = teams_cnt
    out.members_count = members_cnt
    return out

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    id: UUID,
    membership: OrganizationMember = Depends(require_permission("department.delete")),
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(
        Department.id == id,
        Department.organization_id == membership.organization_id
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    dept_name = dept.name
    db.delete(dept)

    log_activity(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        action="department.delete",
        entity_type="department",
        entity_id=id,
        description=f"Deleted department '{dept_name}'"
    )

    db.commit()
    return None
