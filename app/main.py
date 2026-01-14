from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, super_admin, schools, dashboard, teacher
from app.routers.admin import dashboard as admin_dashboard
from app.config import settings

# Note: Database tables will be created on first request or via setup script
# Uncomment the line below if you want to create tables on startup
# Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="School Management System API",
    description="Multi-tenant School Management System Backend",
    version="1.0.0"
)

# CORS middleware (configure for your frontend domain in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
        # Add production frontend URL here when deploying
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(super_admin.router)
app.include_router(schools.router)
app.include_router(dashboard.router)
app.include_router(admin_dashboard.router)  # School Admin Dashboard
app.include_router(teacher.router)  # Teacher Dashboard


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "School Management System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
