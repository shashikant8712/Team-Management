# TEAM MANAGEMENT — LEVEL 1 FULL-STACK APPLICATION

Complete, production-grade Level 1 Multi-Organization Team Management platform built with React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, Alembic, and PostgreSQL.

---

## 1. Project Overview & Level 1 Scope

This system provides a full end-to-end multi-tenant platform for organizations to manage departments, teams, members, roles, permissions, projects, tasks, real-time calculated project progress, and project history.

### Included Features:
- **Authentication & Authorization**: Registration, login, logout, password hashing with bcrypt, JWT bearer tokens, active organization switcher, and role-based access control (RBAC).
- **Organizations**: Create organization, update metadata (logo, timezone, description), isolation across multiple organizations.
- **Roles & Permissions**: Four hierarchical roles (`ADMIN`, `DEPARTMENT_HEAD`, `TEAM_LEADER`, `TEAM_MEMBER`) mapped to 32 granular permissions enforced on backend endpoints.
- **Departments**: Full CRUD, unique department names per organization, assign Department Head, track member and team counts.
- **Teams**: Full CRUD within valid departments, assign Team Leader, add/remove team members.
- **Members Directory**: Add/invite members, assign roles and departments, search and filter by department or role, deactivate members.
- **Projects**: Full CRUD, assign department, team, and project manager, set deadline, priority (`LOW`, `MEDIUM`, `HIGH`), status (`PLANNING`, `NOT_STARTED`, `IN_PROGRESS`, `ON_HOLD`, `COMPLETED`, `ARCHIVED`), and automatic task-based progress tracking.
- **Real Project Progress**: Calculated dynamically:
  $$\text{Progress} = \frac{\text{Completed Tasks}}{\text{Total Tasks}} \times 100$$
  - Completing or reopening a task automatically recalculates and persists project progress.
  - Completing a project manually sets status to `COMPLETED`, progress to `100%`, and sets `completion_date`.
- **Project History**: Preserved archive of `COMPLETED` and `ARCHIVED` projects showing team, manager, completion dates, and full metadata.
- **Tasks**: Full CRUD, assignment to members, due dates, priority (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), status workflow (`TODO` $\rightarrow$ `IN_PROGRESS` $\rightarrow$ `REVIEW` $\rightarrow$ `COMPLETED`).
- **Dashboard**: Real PostgreSQL metrics (Department, Team, Member, Active Project, and Pending Task counts), current active projects with progress bars, upcoming tasks, and recent activity logs.
- **Settings**: User profile update, password change, organization configuration.

---

## 2. Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, React Router v7
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- **Database**: PostgreSQL (`team_management_db`), SQLAlchemy 2.0 ORM
- **Migrations**: Alembic
- **Authentication**: JWT (`PyJWT`), `bcrypt` password hashing
- **Testing**: `pytest`, `httpx`

---

## 3. Project Structure

```
team-management/
│
├── frontend/
│   ├── src/
│   │   ├── components/       # ProtectedRoute, Modals
│   │   ├── layouts/          # AppLayout with sidebar & header
│   │   ├── pages/            # Login, Register, Dashboard, Departments, Teams, Members, Projects, ProjectHistory, Tasks, Settings
│   │   ├── services/         # api.ts (REST client with JWT & Org headers)
│   │   ├── hooks/            # useAuth.tsx (Authentication state & RBAC)
│   │   ├── types/            # TypeScript domain models
│   │   ├── App.tsx           # Router & Route Tree
│   │   ├── main.tsx          # DOM entrypoint
│   │   └── index.css         # Tailwind v4 setup
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint & router aggregation
│   │   ├── core/             # config.py, database.py, security.py
│   │   ├── models/           # SQLAlchemy models (User, Org, Dept, Team, Project, Task, Role, Permission, Activity)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routes/           # REST endpoints
│   │   ├── services/         # activity_service.py, progress_service.py
│   │   └── dependencies/     # auth.py (JWT Bearer & RBAC permission checks)
│   ├── alembic/              # Alembic environment & migrations
│   ├── tests/                # Automated pytest suite
│   ├── seed.py               # Seed system roles, permissions & dev admin
│   ├── requirements.txt
│   └── alembic.ini
│
├── database/
│   └── README.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Setup & Running Instructions

### Step 1: PostgreSQL Setup
Ensure PostgreSQL service is running and `team_management_db` exists:
```bash
psql -U postgres -c "CREATE DATABASE team_management_db;"
```

### Step 2: Backend Setup
```bash
cd backend

# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Run Database Migrations
python -m alembic upgrade head

# 3. Seed System Data (Roles, Permissions & Development Administrator)
python seed.py

# 4. Start Backend Server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 3: Frontend Setup
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start Frontend Server
npm run dev
```

Frontend runs on: `http://localhost:5173`
Backend API Docs: `http://127.0.0.1:8000/docs`

---

## 5. Development Credentials

- **Email**: `admin@teammanagement.com`
- **Password**: `Admin@123456`
*(Or register a new organization directly through the UI)*

---

## 6. Running Automated Tests

Run the complete test suite against PostgreSQL:
```bash
cd backend
python -m pytest tests/ -v
```
All tests verify:
- Registration, Login, Token validation
- Organization isolation across multiple organizations
- Department, Team, Member, Project, Task CRUD
- Real project progress calculations (0% $\rightarrow$ 60% $\rightarrow$ 100%)
- Manual project completion & Project History persistence
