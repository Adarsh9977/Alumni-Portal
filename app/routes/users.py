# routes/users.py - User profile and directory routes

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
import os
import shutil

from ..database import get_db
from ..models import User, Connection
from ..schemas import UserUpdate, UserResponse
from ..dependencies import get_current_user, require_admin
from ..cache import get_or_set, invalidate_namespaces, make_cache_key
# from ..utils.ai_logic import extract_text_from_pdf, calculate_ats_score

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=dict)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "batch": current_user.batch,
        "branch": current_user.branch,
        "company": current_user.company,
        "skills": current_user.skills,
        "bio": current_user.bio,
        "profile_picture": current_user.profile_picture,
        "is_active": current_user.is_active,
        "created_at": str(current_user.created_at) if current_user.created_at else None
    }


@router.put("/me", response_model=dict)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current authenticated user's profile."""
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    invalidate_namespaces("users", "posts", "jobs", "events", "messages")
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "batch": current_user.batch,
            "branch": current_user.branch,
            "company": current_user.company,
            "skills": current_user.skills,
            "bio": current_user.bio,
            "profile_picture": current_user.profile_picture,
            "resume_path": current_user.resume_path,
            "ats_score": current_user.ats_score
        }
    }


@router.post("/profile-picture/upload", response_model=dict)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a profile picture for the current user."""
    # Validate file type
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif')
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and GIF images are supported.")
    
    # Ensure upload directory exists
    upload_dir = "static/profile_pics"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    ext = os.path.splitext(file.filename)[1]
    filename = f"user_{current_user.id}{ext}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    img_url = f"/static/profile_pics/{filename}"
    current_user.profile_picture = img_url
    db.commit()
    invalidate_namespaces("users", "posts", "messages")
    return {"message": "Profile picture updated", "profile_picture": img_url}


@router.delete("/profile-picture/remove", response_model=dict)
def remove_profile_picture(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove the current user's profile picture."""
    current_user.profile_picture = None
    db.commit()
    invalidate_namespaces("users", "posts", "messages")
    return {"message": "Profile picture removed"}


@router.post("/resume/upload", response_model=dict)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a resume PDF, extract text, and calculate ATS score.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Ensure upload directory exists
    upload_dir = "uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"user_{current_user.id}_{file.filename}")
    
    content = await file.read()
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Extract text and analyze
    # text = extract_text_from_pdf(content)
    # analysis = calculate_ats_score(text)
    
    # # Update user record
    # current_user.resume_path = file_path
    # current_user.resume_text = text
    # current_user.ats_score = analysis["score"]
    # current_user.ats_feedback = analysis["feedback"]
    
    # # Also update skills if found
    # if analysis.get("skills"):
    #     existing_skills = current_user.skills.split(",") if current_user.skills else []
    #     new_skills = list(set([s.strip() for s in existing_skills if s.strip()] + analysis["skills"]))
    #     current_user.skills = ", ".join(new_skills)
    
    # Temporarily returning mock data without AI processing
    current_user.resume_path = file_path
    current_user.resume_text = "PDF parsed (AI disabled)"
    current_user.ats_score = 75
    current_user.ats_feedback = "AI Review feature temporarily disabled."
    
    db.commit()
    db.refresh(current_user)
    invalidate_namespaces("users", "jobs")
    
    return {
        "message": "Resume uploaded successfully (AI Analysis Offline)",
        "score": current_user.ats_score,
        "feedback": current_user.ats_feedback,
        "skills_found": []
    }


@router.get("/directory", response_model=List[dict])
def get_alumni_directory(
    batch: Optional[str] = Query(None, description="Filter by batch year"),
    company: Optional[str] = Query(None, description="Filter by company"),
    branch: Optional[str] = Query(None, description="Filter by branch"),
    search: Optional[str] = Query(None, description="Search by name or skills"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the alumni directory with optional filters.
    Lists all alumni users with search and filter capabilities.
    """
    query = db.query(User).filter(User.role == "alumni", User.is_active == True)
    
    if batch:
        query = query.filter(User.batch == batch)
    if company:
        query = query.filter(User.company.ilike(f"%{company}%"))
    if branch:
        query = query.filter(User.branch.ilike(f"%{branch}%"))
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.skills.ilike(f"%{search}%"))
        )
    
    cache_key = make_cache_key(
        "users", "directory", current_user.id,
        batch=batch or "",
        company=company or "",
        branch=branch or "",
        search=search or ""
    )

    def load_directory():
        alumni = query.all()
        alumni_ids = [a.id for a in alumni]
        connections = db.query(Connection).filter(
            or_(
                (Connection.sender_id == current_user.id) & (Connection.receiver_id.in_(alumni_ids)),
                (Connection.sender_id.in_(alumni_ids)) & (Connection.receiver_id == current_user.id)
            )
        ).all() if alumni_ids else []

        connection_by_user = {}
        for conn in connections:
            other_id = conn.receiver_id if conn.sender_id == current_user.id else conn.sender_id
            connection_by_user[other_id] = conn

        results = []
        for a in alumni:
            conn = connection_by_user.get(a.id)
            results.append({
                "id": a.id,
                "name": a.name,
                "email": a.email,
                "batch": a.batch,
                "branch": a.branch,
                "company": a.company,
                "skills": a.skills,
                "bio": a.bio,
                "profile_picture": a.profile_picture,
                "connection_status": conn.status if conn else "none",
                "is_connection_sender": conn.sender_id == current_user.id if conn else False,
                "connection_id": conn.id if conn else None
            })
        return results

    return get_or_set(cache_key, load_directory)


@router.get("/all", response_model=List[dict])
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users - Admin only endpoint."""
    cache_key = make_cache_key("users", "all")
    return get_or_set(
        cache_key,
        lambda: [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "batch": u.batch,
                "branch": u.branch,
                "company": u.company,
                "is_active": u.is_active,
                "created_at": str(u.created_at) if u.created_at else None
            }
            for u in db.query(User).all()
        ]
    )


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user - Admin only endpoint."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    invalidate_namespaces("users", "posts", "jobs", "events", "messages")
    
    return {"message": f"User '{user.name}' deleted successfully"}


@router.put("/{user_id}/toggle-active", response_model=dict)
def toggle_user_active(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle a user's active status - Admin only endpoint."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = not user.is_active
    db.commit()
    invalidate_namespaces("users", "posts", "jobs", "events", "messages")
    
    status_text = "activated" if user.is_active else "deactivated"
    return {"message": f"User '{user.name}' {status_text} successfully"}
