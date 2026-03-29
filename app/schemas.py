# schemas.py - Pydantic schemas for request/response validation

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ==================== AUTH SCHEMAS ====================

class UserRegister(BaseModel):
    """Schema for user registration."""
    name: str
    email: EmailStr
    password: str
    role: str = "student"  # admin, alumni, student


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str
    user: dict


# ==================== USER SCHEMAS ====================

class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = None
    batch: Optional[str] = None
    branch: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: int
    name: str
    email: str
    role: str
    batch: Optional[str] = None
    branch: Optional[str] = None
    company: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    ats_score: Optional[int] = None
    ats_feedback: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== JOB SCHEMAS ====================

class JobCreate(BaseModel):
    """Schema for creating a job posting."""
    title: str
    description: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: Optional[str] = None
    experience_level: Optional[str] = "Entry Level"
    category: Optional[str] = "General"


class JobResponse(BaseModel):
    """Schema for job response data."""
    id: int
    title: str
    description: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: Optional[str] = None
    experience_level: Optional[str] = "Entry Level"
    category: Optional[str] = "General"
    posted_by: int
    poster_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    application_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ==================== EVENT SCHEMAS ====================

class EventCreate(BaseModel):
    """Schema for creating an event."""
    title: str
    description: str
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = None


class EventResponse(BaseModel):
    """Schema for event response data."""
    id: int
    title: str
    description: str
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    organized_by: int
    organizer_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== POST SCHEMAS ====================

class PostCreate(BaseModel):
    """Schema for creating a post."""
    title: Optional[str] = None
    content: str


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str


class CommentResponse(BaseModel):
    """Schema for comment response data."""
    id: int
    content: str
    author_id: int
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Schema for post response data."""
    id: int
    title: Optional[str] = None
    content: str
    author_id: int
    author_name: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    like_count: Optional[int] = 0
    is_liked: Optional[bool] = False
    comments: Optional[List[CommentResponse]] = []

    class Config:
        from_attributes = True


# ==================== APPLICATION SCHEMAS ====================

class ApplicationCreate(BaseModel):
    """Schema for applying to a job."""
    job_id: int
    cover_letter: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Schema for application response data."""
    id: int
    job_id: int
    job_title: Optional[str] = None
    applicant_id: int
    applicant_name: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""
    status: str  # pending, reviewed, accepted, rejected


# ==================== CONNECTION SCHEMAS ====================

class ConnectionCreate(BaseModel):
    """Schema for sending a connection request."""
    receiver_id: int


class ConnectionUpdate(BaseModel):
    """Schema for updating connection status."""
    status: str  # accepted, rejected


class ConnectionResponse(BaseModel):
    """Schema for connection response data."""
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: Optional[datetime] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None

    class Config:
        from_attributes = True
