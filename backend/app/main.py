from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# Import routers
from app.routes.auth import router as auth_router
from app.routes.organizations import router as org_router
from app.routes.departments import router as dept_router
from app.routes.teams import router as team_router
from app.routes.members import router as member_router
from app.routes.projects import router as project_router
from app.routes.tasks import router as task_router
from app.routes.dashboard import router as dashboard_router
from app.routes.activities import router as activity_router
from app.routes.settings import router as settings_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Level 1 Multi-Organization Team Management Platform API",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(org_router, prefix="/api")
app.include_router(dept_router, prefix="/api")
app.include_router(team_router, prefix="/api")
app.include_router(member_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(activity_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API (Level 1)",
        "docs": "/docs",
        "health": "/api/health",
    }
