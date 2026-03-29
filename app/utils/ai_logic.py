# utils/ai_logic.py - AI Logic for Resume Analysis and Job Recommendation

import re
from typing import List, Dict, Any
from pypdf import PdfReader
import io

# Common Keywords for ATS Analysis
SKILL_KEYWORDS = [
    "python", "javascript", "react", "fastapi", "sql", "aws", "docker", "kubernetes",
    "machine learning", "data science", "backend", "frontend", "fullstack",
    "project management", "agile", "git", "java", "c++", "leadership", "communication"
]

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file byte stream."""
    try:
        reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception:
        return ""

def calculate_ats_score(resume_text: str, job_requirements: str = None) -> Dict[str, Any]:
    """
    Calculate an ATS score based on keyword matching and formatting.
    If job_requirements is provided, it calculates a match score.
    """
    if not resume_text:
        return {"score": 0, "feedback": "Could not read resume text."}

    resume_text = resume_text.lower()
    found_skills = []
    
    # Check for core skills
    for skill in SKILL_KEYWORDS:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text):
            found_skills.append(skill)
    
    # Basic scoring logic
    score = min(len(found_skills) * 8, 100) # Each skill adds 8 points
    
    # Check for sections
    sections = ["experience", "education", "projects", "skills"]
    missing_sections = []
    for section in sections:
        if section not in resume_text:
            score -= 5
            missing_sections.append(section.capitalize())
    
    feedback = f"Found skills: {', '.join(found_skills[:10])}. "
    if missing_sections:
        feedback += f"Your resume might be missing these sections: {', '.join(missing_sections)}. "
    else:
        feedback += "Great! Your resume has all standard sections. "
        
    if score < 50:
        feedback += "Try adding more industry-specific keywords and ensuring clear headings."
    elif score < 80:
        feedback += "Good job! To reach a top score, quantify your achievements with numbers."
    else:
        feedback += "Excellent! Your resume is highly optimized for ATS systems."
        
    return {
        "score": max(score, 0),
        "feedback": feedback,
        "skills": found_skills
    }

def get_job_recommendations(user_skills: List[str], jobs: List[Any]) -> List[Dict[str, Any]]:
    """
    Rank jobs based on matching user skills.
    """
    recommendations = []
    
    for job in jobs:
        match_count = 0
        job_content = (job.title + " " + job.description + " " + (job.requirements or "")).lower()
        
        for skill in user_skills:
            if skill.lower() in job_content:
                match_count += 1
        
        # Calculate percentage match
        total_relevant = len(user_skills) if user_skills else 1
        match_percentage = int((match_count / total_relevant) * 100) if user_skills else 0
        
        if match_percentage > 10: # Only suggest if there is some relevance
            recommendations.append({
                "job_id": job.id,
                "match_score": match_percentage,
                "reason": f"Matches {match_count} of your key skills."
            })
            
    # Sort by match score descending
    return sorted(recommendations, key=lambda x: x['match_score'], reverse=True)
