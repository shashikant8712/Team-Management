import sys
import uuid
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role, Permission, RolePermission
from app.models.user import User

ALL_PERMISSIONS = [
    # Organization
    ("organization.view", "View organization details"),
    ("organization.create", "Create new organization"),
    ("organization.edit", "Edit organization details"),
    
    # Department
    ("department.view", "View departments"),
    ("department.create", "Create departments"),
    ("department.edit", "Edit departments"),
    ("department.delete", "Delete departments"),
    
    # Team
    ("team.view", "View teams"),
    ("team.create", "Create teams"),
    ("team.edit", "Edit teams"),
    ("team.delete", "Delete teams"),
    ("team.assign", "Assign members to teams"),
    
    # Member
    ("member.view", "View members"),
    ("member.create", "Add/invite new members"),
    ("member.edit", "Edit member details and role"),
    ("member.delete", "Deactivate/remove members"),
    ("member.assign", "Assign member to department/team"),
    
    # Project
    ("project.view", "View projects"),
    ("project.create", "Create projects"),
    ("project.edit", "Edit project details"),
    ("project.delete", "Delete projects"),
    ("project.assign", "Assign members/teams to projects"),
    ("project.complete", "Mark projects as completed"),
    ("project.archive", "Archive projects"),
    
    # Task
    ("task.view", "View tasks"),
    ("task.create", "Create tasks"),
    ("task.edit", "Edit tasks"),
    ("task.delete", "Delete tasks"),
    ("task.assign", "Assign tasks to members"),
    ("task.update_status", "Update task status (complete/reopen)"),
    
    # Dashboard & Activity
    ("dashboard.view", "View dashboard metrics"),
    ("activity.view", "View organization activity logs"),
]

ROLE_PERMISSIONS_MAP = {
    "ADMIN": [p[0] for p in ALL_PERMISSIONS],
    "DEPARTMENT_HEAD": [
        "organization.view",
        "department.view", "department.edit",
        "team.view", "team.create", "team.edit", "team.assign",
        "member.view", "member.assign",
        "project.view", "project.create", "project.edit", "project.assign", "project.complete",
        "task.view", "task.create", "task.edit", "task.assign", "task.update_status",
        "dashboard.view", "activity.view"
    ],
    "TEAM_LEADER": [
        "organization.view",
        "department.view",
        "team.view",
        "member.view",
        "project.view", "project.assign",
        "task.view", "task.create", "task.edit", "task.delete", "task.assign", "task.update_status",
        "dashboard.view", "activity.view"
    ],
    "TEAM_MEMBER": [
        "organization.view",
        "team.view",
        "member.view",
        "project.view",
        "task.view", "task.update_status",
        "dashboard.view"
    ],
}

def seed_system_data(create_dev_admin: bool = True):
    db = SessionLocal()
    try:
        print("[INFO] Seeding roles and permissions...")
        
        # 1. Seed Permissions
        perm_objs = {}
        for code, desc in ALL_PERMISSIONS:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if not perm:
                perm = Permission(code=code, description=desc)
                db.add(perm)
                db.flush()
            perm_objs[code] = perm

        # 2. Seed Roles
        role_objs = {}
        for role_name, perms in ROLE_PERMISSIONS_MAP.items():
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=f"{role_name.replace('_', ' ').title()} role with defined Level 1 permissions"
                )
                db.add(role)
                db.flush()
            role_objs[role_name] = role

            # Ensure role permissions mapped
            existing_rp = {
                rp.permission_id for rp in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()
            }
            for code in perms:
                p_id = perm_objs[code].id
                if p_id not in existing_rp:
                    rp = RolePermission(role_id=role.id, permission_id=p_id)
                    db.add(rp)

        # 3. Optional Dev Administrator
        if create_dev_admin:
            dev_email = "admin@teammanagement.com"
            admin_user = db.query(User).filter(User.email == dev_email).first()
            if not admin_user:
                admin_user = User(
                    name="System Administrator",
                    email=dev_email,
                    password_hash=hash_password("Admin@123456"),
                    phone="+1-555-0199",
                    status="ACTIVE"
                )
                db.add(admin_user)
                print(f"[INFO] Created Development Administrator: {dev_email} / Admin@123456")

        db.commit()
        print("[SUCCESS] System roles and permissions initialized successfully.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding system data: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    create_admin = "--no-dev-admin" not in sys.argv
    seed_system_data(create_dev_admin=create_admin)
