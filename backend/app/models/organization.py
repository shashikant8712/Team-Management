import uuid
from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey, func, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    organization_type = Column(String(50), nullable=False, default="COMPANY")  # COMPANY, COLLEGE, OTHER
    description = Column(Text, nullable=True)
    logo = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("organization_type IN ('COMPANY', 'COLLEGE', 'OTHER')", name="check_org_type"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="check_org_status"),
    )

    creator = relationship("User", back_populates="created_organizations", foreign_keys=[created_by])
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="organization", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="organization", cascade="all, delete-orphan")

class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    joining_date = Column(Date, default=func.current_date(), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="check_org_member_status"),
    )

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")
    role = relationship("Role", back_populates="members")
    department = relationship("Department", back_populates="members")
