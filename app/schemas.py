from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional
from datetime import datetime
import re

class IntakeJob(BaseModel):
    """
    Job posting creation request.
    
    Creates a new job posting with requirements and preferences.
    """
    title: str = Field(..., min_length=1, max_length=200, description="Job title", example="Senior Full Stack Engineer")
    jd_text: str = Field(..., min_length=10, max_length=10000, description="Detailed job description", example="We are looking for a senior full stack engineer to join our team...")
    must_have: List[str] = Field(default=[], max_items=20, description="Required technical skills", example=["Python", "React", "PostgreSQL"])
    nice_to_have: List[str] = Field(default=[], max_items=20, description="Preferred but not required skills", example=["Docker", "AWS", "Machine Learning"])
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Job title cannot be empty')
        return v.strip()
    
    @validator('jd_text')
    def validate_jd_text(cls, v):
        if not v.strip():
            raise ValueError('Job description cannot be empty')
        return v.strip()
    
    @validator('must_have', 'nice_to_have')
    def validate_skills(cls, v):
        if v:
            # Remove empty strings and trim whitespace
            cleaned = [skill.strip() for skill in v if skill.strip()]
            # Validate each skill
            for skill in cleaned:
                if len(skill) > 100:
                    raise ValueError(f'Skill "{skill}" is too long (max 100 characters)')
            return cleaned
        return v

class IntakeCandidate(BaseModel):
    """
    Candidate registration request.
    
    Registers a new candidate with their resume and contact information.
    """
    name: str = Field(..., min_length=1, max_length=200, description="Full name of the candidate", example="John Doe")
    email: EmailStr = Field(..., description="Primary email address", example="john.doe@example.com")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number", example="+1-555-123-4567")
    resume_text: Optional[str] = Field(None, max_length=50000, description="Resume content as plain text", example="John Doe\nSoftware Engineer\n5 years experience...")
    resume_url: Optional[str] = Field(None, max_length=500, description="URL to resume file (PDF, DOC, etc.)", example="https://example.com/resume.pdf")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Basic phone validation - remove all non-digit characters except + at start
            cleaned = re.sub(r'[^\d+]', '', v)
            if not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', v):
                raise ValueError('Invalid phone number format')
            return cleaned
        return v
    
    @validator('resume_url')
    def validate_resume_url(cls, v):
        if v:
            if not re.match(r'^https?://', v):
                raise ValueError('Resume URL must start with http:// or https://')
        return v

class MatchRequest(BaseModel):
    """
    Candidate-job matching request.
    
    Triggers AI-powered matching between a candidate and a job posting.
    """
    job_id: int = Field(..., gt=0, description="ID of the job posting", example=1)
    candidate_id: int = Field(..., gt=0, description="ID of the candidate", example=1)

class InviteRequest(BaseModel):
    application_id: int = Field(..., gt=0, description="Application ID")

class ConfirmRequest(BaseModel):
    application_id: int = Field(..., gt=0, description="Application ID")
    slot_iso_start: str = Field(..., description="Start time in ISO format")
    slot_iso_end: str = Field(..., description="End time in ISO format")
    
    @validator('slot_iso_start', 'slot_iso_end')
    def validate_iso_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid ISO datetime format')

# Authentication Schemas
class AdminLogin(BaseModel):
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=6, max_length=100, description="Admin password")

class AdminResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None

# Response Models
class JobResponse(BaseModel):
    """
    Job posting response.
    
    Returns job information after creation or retrieval.
    """
    id: int = Field(..., description="Unique job ID", example=1)
    title: str = Field(..., description="Job title", example="Senior Full Stack Engineer")
    created_at: datetime = Field(..., description="Job creation timestamp", example="2024-01-15T10:30:00Z")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Senior Full Stack Engineer",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class CandidateResponse(BaseModel):
    """
    Candidate response.
    
    Returns candidate information after registration or retrieval.
    """
    id: int = Field(..., description="Unique candidate ID", example=1)
    name: str = Field(..., description="Full name", example="John Doe")
    email: str = Field(..., description="Email address", example="john.doe@example.com")
    phone: Optional[str] = Field(None, description="Phone number", example="+1-555-123-4567")
    created_at: datetime = Field(..., description="Registration timestamp", example="2024-01-15T10:30:00Z")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    fit_score: Optional[float] = None
    fit_status: Optional[str] = None
    reasons: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class InterviewLinkResponse(BaseModel):
    id: int
    application_id: int
    token: str
    status: str
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
