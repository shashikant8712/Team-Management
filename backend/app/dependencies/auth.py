from typing import Optional, List
from uuid import UUID
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.role import Role, Permission, RolePermission

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identification in token",
        )

    user = db.query(User).filter(User.id == user_id, User.status == "ACTIVE").first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is inactive",
        )
    return user

def get_current_membership(
    user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    db: Session = Depends(get_db)
) -> OrganizationMember:
    # If organization ID header provided, check membership in that org
    target_org_id = None
    if x_organization_id:
        try:
            target_org_id = UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID provided in X-Organization-Id header",
            )

    query = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.status == "ACTIVE"
    )

    if target_org_id:
        membership = query.filter(OrganizationMember.organization_id == target_org_id).first()
    else:
        membership = query.first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an active member of this organization",
        )

    return membership

def require_permission(permission_code: str):
    def permission_checker(
        membership: OrganizationMember = Depends(get_current_membership),
        db: Session = Depends(get_db)
    ) -> OrganizationMember:
        role = db.query(Role).filter(Role.id == membership.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assigned role not found",
            )

        # ADMIN always has full permission
        if role.name == "ADMIN":
            return membership

        # Check role_permissions
        has_perm = db.query(RolePermission).join(
            Permission, RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id == role.id,
            Permission.code == permission_code
        ).first()

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission_code}' required",
            )

        return membership

    return permission_checker
