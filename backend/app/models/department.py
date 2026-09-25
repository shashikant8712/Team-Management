import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    department_head_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_dept_name"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="check_department_status"),
    )

    organization = relationship("Organization", back_populates="departments")
    head = relationship("User", foreign_keys=[department_head_id])
    members = relationship("OrganizationMember", back_populates="department")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="department")
