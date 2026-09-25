# Database Architecture & Documentation

## Database Information
- **RDBMS**: PostgreSQL
- **Database Name**: `team_management_db`
- **ORM**: SQLAlchemy 2.0
- **Migration Engine**: Alembic

## Core Level 1 Tables

1. **`users`**
   - Stores user accounts with bcrypt hashed passwords (`password_hash`), names, emails, phones, profile photos, and status (`ACTIVE`, `INACTIVE`).
   - Email is unique and indexed. `password_hash` is never exposed in API schemas.

2. **`organizations`**
   - Multi-tenant organization records.
   - Types: `COMPANY`, `COLLEGE`, `OTHER`.
   - Stores name, logo, timezone, status, and owner reference (`created_by`).

3. **`organization_members`**
   - Links users to organizations with assigned role and department.
   - Unique constraint: `(organization_id, user_id)`.
   - Enforces single active role per organization.

4. **`roles`**
   - Level 1 system roles: `ADMIN`, `DEPARTMENT_HEAD`, `TEAM_LEADER`, `TEAM_MEMBER`.

5. **`permissions`**
   - Granular permission strings for RBAC enforcement (e.g., `department.create`, `project.complete`, `task.assign`).

6. **`role_permissions`**
   - Junction table linking roles to granted permissions.

7. **`departments`**
   - Functional units within an organization with assigned department head.
   - Unique constraint: `(organization_id, name)`.

8. **`teams`**
   - Sub-units belonging to a department within the same organization with assigned team leader.
   - Unique constraint: `(organization_id, department_id, name)`.

9. **`team_members`**
   - Junction table of users assigned to teams.
   - Unique constraint: `(team_id, user_id)`.

10. **`projects`**
    - Project records with department, team, project manager, priority (`LOW`, `MEDIUM`, `HIGH`), status (`PLANNING`, `NOT_STARTED`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, `ARCHIVED`), and calculated progress `(0 - 100)`.
    - Stores `completion_date` and `archive_date` for project history preservation.

11. **`project_members`**
    - Junction table assigning members to projects.
    - Unique constraint: `(project_id, user_id)`.

12. **`tasks`**
    - Actionable work items attached to a project.
    - Status: `TODO`, `IN_PROGRESS`, `REVIEW`, `COMPLETED`.
    - Priority: `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
    - Recalculates parent project progress upon status changes.

13. **`activity_logs`**
    - Audit log recording entity actions across the organization for dashboard feeds.

## Setup & Migration Commands

```bash
# 1. Run Migrations
alembic upgrade head

# 2. Seed System Roles and Permissions
python seed.py
```
