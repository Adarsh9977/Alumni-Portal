# routes/resume.py - AI Resume Analyzer and Optimizer
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
import os
import shutil
from pypdf import PdfReader
import re

from ..database import get_db
from ..models import User
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/resume", tags=["Resume Analyzer"])

# Keyword focus for Career Audit
TECHNICAL_KEYWORDS = {
    "Python": 5, "Java": 5, "Javascript": 5, "React": 5, "Node.js": 5, "SQL": 5,
    "AWS": 5, "Cloud": 5, "Machine Learning": 5, "AI": 5, "Data Science": 5,
    "Docker": 5, "Kubernetes": 5, "Project Management": 5, "Leadership": 5
}

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and analyze a resume PDF using AI heuristics."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save the file (Simulated path for now)
    upload_dir = "uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"user_{current_user.id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract Text
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        
        # Analyze Content (Simulated AI)
        score = 0
        found_skills = []
        
        # Check for keywords
        for skill, weight in TECHNICAL_KEYWORDS.items():
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.I):
                score += weight
                found_skills.append(skill)
        
        # Length check
        if len(text) > 2000: score += 15
        elif len(text) > 1000: score += 10
        
        # Formatting check (Basic)
        if "Experience" in text or "Projects" in text: score += 15
        if "Education" in text: score += 10
        if "Contact" in text or "Email" in text: score += 10
        
        # Normalize score (Cap at 100)
        final_score = min(score + 25, 100) # Base 25
        
        # Generate Feedback
        feedback = []
        if final_score < 50:
            feedback.append("⚠️ Your resume lacks technical keywords. Add specific skills like Python, AWS, or React if applicable.")
        if "Experience" not in text:
            feedback.append("⚠️ Missing 'Experience' section. Highlighting your past work or internships is critical.")
        if final_score > 80:
            feedback.append("✅ Excellent resume! Your profile has strong keyword density and clear structure.")
        elif final_score > 60:
            feedback.append("📝 Good start. Consider adding more quantifiable results (e.g., 'Improved performance by 20%').")
        
        # Update User Model
        current_user.resume_path = file_path
        current_user.resume_text = text[:1000] # Save snippet
        current_user.ats_score = final_score
        current_user.ats_feedback = "\n".join(feedback)
        
        db.commit()
        db.refresh(current_user)
        
        return {
            "score": final_score,
            "feedback": current_user.ats_feedback,
            "skills_detected": found_skills
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/status")
def get_resume_status(current_user: User = Depends(get_current_user)):
    """Check the current status of the user's resume analysis."""
    return {
        "has_resume": current_user.resume_path is not None,
        "score": current_user.ats_score,
        "feedback": current_user.ats_feedback
    }
