# main.py - FastAPI application entry point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import engine, Base
from app.routes import auth, users, jobs, events, posts, connections, resume

# Skip create_all entirely to prevent lambda hanging on boot
# Database schema was already manually created via seed_data.py

# Initialize FastAPI application
app = FastAPI(
    title="Alumni Nexus Portal",
    description="A comprehensive alumni portal with job postings, events, and social features",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route modules with explicit prefixes just to be sure
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(events.router)
app.include_router(posts.router)
app.include_router(connections.router)
app.include_router(resume.router)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
profile_pics_dir = os.path.join(static_root, "profile_pics")
try:
    os.makedirs(profile_pics_dir, exist_ok=True)
except Exception:
    pass

# Mount specific folders to avoid conflicts
if os.path.exists(profile_pics_dir):
    app.mount("/static/profile_pics", StaticFiles(directory=profile_pics_dir), name="profile_pics")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Also keep /uploads for future-proofing
if os.path.exists(static_root):
    app.mount("/uploads", StaticFiles(directory=static_root), name="uploads")


# ==================== FRONTEND PAGE ROUTES ====================

@app.get("/")
async def serve_index():
    """Serve the landing page."""
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/login")
async def serve_login():
    """Serve the login page."""
    return FileResponse(os.path.join(frontend_dir, "login.html"))


@app.get("/register")
async def serve_register():
    """Serve the registration page."""
    return FileResponse(os.path.join(frontend_dir, "register.html"))


@app.get("/dashboard")
async def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))


@app.get("/jobs")
async def serve_jobs():
    """Serve the jobs page."""
    return FileResponse(os.path.join(frontend_dir, "jobs.html"))


@app.get("/events")
async def serve_events():
    """Serve the events page."""
    return FileResponse(os.path.join(frontend_dir, "events.html"))


@app.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "app": "Alumni Nexus Portal"}
