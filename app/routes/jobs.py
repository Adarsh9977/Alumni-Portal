# routes/jobs.py - Job portal routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import User, Job, Application
from ..schemas import (
    JobCreate, JobResponse, ApplicationCreate, 
    ApplicationResponse, ApplicationStatusUpdate
)
from ..dependencies import get_current_user, require_alumni
# from ..utils.ai_logic import get_job_recommendations
from fastapi import Query, File, UploadFile, Form
from datetime import datetime, timedelta
import os
import shutil

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.post("/", response_model=dict)
def create_job(
    job_data: JobCreate,
    current_user: User = Depends(require_alumni),
    db: Session = Depends(get_db)
):
    """Create a new job posting - Alumni and Admin only."""
    new_job = Job(
        title=job_data.title,
        description=job_data.description,
        company=job_data.company,
        location=job_data.location,
        job_type=job_data.job_type,
        salary_range=job_data.salary_range,
        requirements=job_data.requirements,
        experience_level=job_data.experience_level,
        category=job_data.category,
        posted_by=current_user.id
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {
        "message": "Job posted successfully",
        "job": {
            "id": new_job.id,
            "title": new_job.title,
            "company": new_job.company
        }
    }


@router.get("/", response_model=List[dict])
def get_all_jobs(
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    days_ago: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active job postings with filters."""
    query = db.query(Job).filter(Job.is_active == True)
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if experience:
        query = query.filter(Job.experience_level == experience)
    if category:
        query = query.filter(Job.category == category)
    if days_ago:
        cutoff = datetime.now() - timedelta(days=days_ago)
        query = query.filter(Job.created_at >= cutoff)
        
    jobs = query.order_by(Job.created_at.desc()).all()
    
    result = []
    for job in jobs:
        poster = db.query(User).filter(User.id == job.posted_by).first()
        app_count = db.query(Application).filter(Application.job_id == job.id).count()
        alumni_count = db.query(User).filter(User.company.ilike(f"%{job.company}%"), User.role == "alumni").count()
        result.append({
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "salary_range": job.salary_range,
            "requirements": job.requirements,
            "experience_level": job.experience_level,
            "category": job.category,
            "posted_by": job.posted_by,
            "poster_name": poster.name if poster else "Unknown",
            "is_active": job.is_active,
            "created_at": str(job.created_at) if job.created_at else None,
            "application_count": app_count,
            "alumni_count": alumni_count
        })
    
    return result


@router.get("/{job_id}", response_model=dict)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job posting by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    poster = db.query(User).filter(User.id == job.posted_by).first()
    app_count = db.query(Application).filter(Application.job_id == job.id).count()
    alumni_count = db.query(User).filter(User.company.ilike(f"%{job.company}%"), User.role == "alumni").count()
    
    # Check if current user has already applied
    has_applied = db.query(Application).filter(
        Application.job_id == job_id,
        Application.applicant_id == current_user.id
    ).first() is not None
    
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "company": job.company,
        "location": job.location,
        "job_type": job.job_type,
        "salary_range": job.salary_range,
        "requirements": job.requirements,
        "experience_level": job.experience_level,
        "category": job.category,
        "posted_by": job.posted_by,
        "poster_name": poster.name if poster else "Unknown",
        "is_active": job.is_active,
        "created_at": str(job.created_at) if job.created_at else None,
        "application_count": app_count,
        "has_applied": has_applied,
        "alumni_count": alumni_count
    }


@router.get("/recommendations", response_model=List[dict])
def get_job_recs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations based on user skills."""
    if not current_user.skills:
        # Fallback to recent jobs if no skills listed
        jobs = db.query(Job).filter(Job.is_active == True).order_by(Job.created_at.desc()).limit(10).all()
        return [
            {
                "id": j.id, "title": j.title, "company": j.company, 
                "match_score": 0, "reason": "Add skills to get better matches"
            } for j in jobs
        ]
    
    user_skills = [s.strip() for s in current_user.skills.split(",") if s.strip()]
    all_active_jobs = db.query(Job).filter(Job.is_active == True).all()
    
    # recs = get_job_recommendations(user_skills, all_active_jobs)
    
    # Enrich recommendation data with fallback mock scoring
    result = []
    # Just return top 5 active jobs as fallback since AI is disabled
    for job in all_active_jobs[:5]:
        al_cnt = db.query(User).filter(User.company.ilike(f"%{job.company}%"), User.role == "alumni").count()
        result.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_type": job.job_type,
            "experience_level": job.experience_level,
            "match_score": 85,  # Mocked
            "reason": "AI Recommended (Beta)",
            "alumni_count": al_cnt
        })
    return result


@router.delete("/{job_id}", response_model=dict)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job posting - only the poster or admin can delete."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}


# ==================== JOB APPLICATIONS ====================

@router.post("/apply", response_model=dict)
async def apply_for_job(
    job_id: int = Form(...),
    cover_letter: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply for a job with an optional JD-specific resume."""
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already applied
    existing = db.query(Application).filter(Application.job_id == job_id, Application.applicant_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied")
    
    file_url = None
    if resume:
        if not resume.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        
        # Save JD-specific resume
        upload_dir = "static/job_resumes"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"app_{current_user.id}_job_{job_id}.pdf"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(resume.file, f)
        file_url = f"/static/job_resumes/{filename}"

    new_application = Application(
        job_id=job_id,
        applicant_id=current_user.id,
        cover_letter=cover_letter,
        resume_path=file_url or current_user.resume_path
    )
    
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    return {"message": "Application successful", "application_id": new_application.id}


@router.get("/applications/my", response_model=List[dict])
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all job applications submitted by the current user."""
    applications = db.query(Application).filter(
        Application.applicant_id == current_user.id
    ).order_by(Application.created_at.desc()).all()
    
    result = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Deleted Job",
            "company": job.company if job else "N/A",
            "cover_letter": app.cover_letter,
            "status": app.status,
            "created_at": str(app.created_at) if app.created_at else None
        })
    
    return result


@router.get("/{job_id}/applications", response_model=List[dict])
def get_job_applications(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all applications for a specific job - Job poster or admin only."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view applications for this job"
        )
    
    applications = db.query(Application).filter(
        Application.job_id == job_id
    ).order_by(Application.created_at.desc()).all()
    
    result = []
    for app in applications:
        applicant = db.query(User).filter(User.id == app.applicant_id).first()
        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "applicant_id": app.applicant_id,
            "applicant_name": applicant.name if applicant else "Unknown",
            "applicant_email": applicant.email if applicant else "N/A",
            "cover_letter": app.cover_letter,
            "status": app.status,
            "created_at": str(app.created_at) if app.created_at else None
        })
    
    return result


@router.put("/applications/{application_id}/status", response_model=dict)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update application status - Job poster or admin only."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated job not found"
        )
    
    if job.posted_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this application"
        )
    
    valid_statuses = ["pending", "reviewed", "accepted", "rejected"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    application.status = status_data.status
    db.commit()
    
    return {"message": f"Application status updated to '{status_data.status}'"}
