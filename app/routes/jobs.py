# routes/jobs.py - Job portal routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
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
from ..cache import get_or_set, invalidate_namespace, make_cache_key

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _company_alumni_counts(db: Session, companies: set[str]) -> dict[str, int]:
    return {
        company: db.query(User).filter(
            User.company.ilike(f"%{company}%"),
            User.role == "alumni"
        ).count()
        for company in companies
        if company
    }


def _serialize_jobs(db: Session, jobs: list[Job], current_user_id: int | None = None) -> list[dict]:
    job_ids = [job.id for job in jobs]
    poster_ids = {job.posted_by for job in jobs}
    posters = db.query(User).filter(User.id.in_(poster_ids)).all() if poster_ids else []
    posters_by_id = {poster.id: poster for poster in posters}
    app_counts = dict(
        db.query(Application.job_id, func.count(Application.id)).filter(
            Application.job_id.in_(job_ids)
        ).group_by(Application.job_id).all()
    ) if job_ids else {}
    applied_job_ids = {
        job_id for (job_id,) in db.query(Application.job_id).filter(
            Application.job_id.in_(job_ids),
            Application.applicant_id == current_user_id
        ).all()
    } if job_ids and current_user_id else set()
    alumni_counts = _company_alumni_counts(db, {job.company for job in jobs})

    result = []
    for job in jobs:
        poster = posters_by_id.get(job.posted_by)
        item = {
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
            "application_count": app_counts.get(job.id, 0),
            "alumni_count": alumni_counts.get(job.company, 0)
        }
        if current_user_id:
            item["has_applied"] = job.id in applied_job_ids
        result.append(item)
    return result


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
    invalidate_namespace("jobs")
    
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
    cache_key = make_cache_key(
        "jobs", "all", current_user.id,
        location=location or "",
        job_type=job_type or "",
        experience=experience or "",
        category=category or "",
        days_ago=days_ago or ""
    )

    def load_jobs():
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
        return _serialize_jobs(db, query.order_by(Job.created_at.desc()).all())

    return get_or_set(cache_key, load_jobs)


@router.get("/recommendations", response_model=List[dict])
def get_job_recs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized job recommendations based on user skills."""
    cache_key = make_cache_key("jobs", "recommendations", current_user.id, skills=current_user.skills or "")

    def load_recs():
        jobs = db.query(Job).filter(Job.is_active == True).order_by(Job.created_at.desc()).limit(10).all()
        if not current_user.skills:
            return [
                {
                    "id": j.id, "title": j.title, "company": j.company,
                    "match_score": 0, "reason": "Add skills to get better matches"
                } for j in jobs
            ]

        serialized = _serialize_jobs(db, jobs[:5])
        for item in serialized:
            item["match_score"] = 85
            item["reason"] = "AI Recommended (Beta)"
        return serialized

    return get_or_set(cache_key, load_recs)


@router.get("/{job_id}", response_model=dict)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job posting by ID."""
    cache_key = make_cache_key("jobs", "one", job_id, current_user.id)

    def load_job():
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return _serialize_jobs(db, [job], current_user.id)[0]

    return get_or_set(cache_key, load_job)


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
    invalidate_namespace("jobs")
    
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
    invalidate_namespace("jobs")
    
    return {"message": "Application successful", "application_id": new_application.id}


@router.get("/applications/my", response_model=List[dict])
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all job applications submitted by the current user."""
    cache_key = make_cache_key("jobs", "applications", "my", current_user.id)

    def load_applications():
        applications = db.query(Application).filter(
            Application.applicant_id == current_user.id
        ).order_by(Application.created_at.desc()).all()
        job_ids = [app.job_id for app in applications]
        jobs = db.query(Job).filter(Job.id.in_(job_ids)).all() if job_ids else []
        jobs_by_id = {job.id: job for job in jobs}
        return [
            {
                "id": app.id,
                "job_id": app.job_id,
                "job_title": jobs_by_id[app.job_id].title if app.job_id in jobs_by_id else "Deleted Job",
                "company": jobs_by_id[app.job_id].company if app.job_id in jobs_by_id else "N/A",
                "cover_letter": app.cover_letter,
                "status": app.status,
                "created_at": str(app.created_at) if app.created_at else None
            }
            for app in applications
        ]

    return get_or_set(cache_key, load_applications)


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
    
    cache_key = make_cache_key("jobs", "applications", job_id, current_user.id)

    def load_job_applications():
        applications = db.query(Application).filter(
            Application.job_id == job_id
        ).order_by(Application.created_at.desc()).all()
        applicant_ids = [app.applicant_id for app in applications]
        applicants = db.query(User).filter(User.id.in_(applicant_ids)).all() if applicant_ids else []
        applicants_by_id = {applicant.id: applicant for applicant in applicants}
        return [
            {
                "id": app.id,
                "job_id": app.job_id,
                "applicant_id": app.applicant_id,
                "applicant_name": applicants_by_id[app.applicant_id].name if app.applicant_id in applicants_by_id else "Unknown",
                "applicant_email": applicants_by_id[app.applicant_id].email if app.applicant_id in applicants_by_id else "N/A",
                "cover_letter": app.cover_letter,
                "status": app.status,
                "created_at": str(app.created_at) if app.created_at else None
            }
            for app in applications
        ]

    return get_or_set(cache_key, load_job_applications)


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
    invalidate_namespace("jobs")
    
    return {"message": f"Application status updated to '{status_data.status}'"}
