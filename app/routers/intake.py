from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from ..services.auth import get_current_admin
from ..services.logger import log_business_event, log_error
from ..services.resume_parser import resume_parser
from ..services.cache import cache_service, CacheKeys

router = APIRouter(prefix="/intake", tags=["intake"])

@router.post("/job", response_model=schemas.JobResponse)
def create_job(
    payload: schemas.IntakeJob, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    try:
        job = models.Job(title=payload.title, jd_text=payload.jd_text,
                         jd_json={"must_have": payload.must_have, "nice_to_have": payload.nice_to_have})
        db.add(job); db.commit(); db.refresh(job)
        
        log_business_event("job_created", "job", job.id, 
                          admin_id=current_admin.id, title=payload.title)
        
        # Invalidate related cache entries
        cache_service.invalidate_related("job", job.id)
        
        return job
    except Exception as e:
        log_error(e, context={"operation": "create_job", "admin_id": current_admin.id})
        raise

@router.post("/candidate", response_model=schemas.CandidateResponse)
async def create_candidate(
    payload: schemas.IntakeCandidate, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    try:
        # Parse resume if provided
        resume_data = {"skills": []}
        if payload.resume_url:
            parsed_resume = await resume_parser.parse_resume_from_url(payload.resume_url)
            resume_data = {
                "skills": parsed_resume.get("skills", []),
                "experience": parsed_resume.get("experience", []),
                "education": parsed_resume.get("education", []),
                "text": parsed_resume.get("text", "")
            }
        elif payload.resume_text:
            parsed_resume = await resume_parser.parse_resume_from_text(payload.resume_text)
            resume_data = {
                "skills": parsed_resume.get("skills", []),
                "experience": parsed_resume.get("experience", []),
                "education": parsed_resume.get("education", []),
                "text": parsed_resume.get("text", payload.resume_text)
            }
        
        cand = models.Candidate(
            name=payload.name, 
            email=payload.email, 
            phone=payload.phone,
            resume_url=payload.resume_url, 
            resume_json=resume_data
        )
        db.add(cand); db.commit(); db.refresh(cand)
        
        log_business_event("candidate_created", "candidate", cand.id,
                          admin_id=current_admin.id, name=payload.name, email=payload.email,
                          skills_count=len(resume_data.get("skills", [])))
        
        # Invalidate related cache entries
        cache_service.invalidate_related("candidate", cand.id)
        
        return cand
    except Exception as e:
        log_error(e, context={"operation": "create_candidate", "admin_id": current_admin.id})
        raise

@router.get("/jobs", response_model=List[schemas.JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Get all jobs."""
    try:
        jobs = db.query(models.Job).all()
        return jobs
    except Exception as e:
        log_error(e, context={"operation": "get_jobs", "admin_id": current_admin.id})
        raise

@router.get("/candidates", response_model=List[schemas.CandidateResponse])
def get_candidates(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Get all candidates."""
    try:
        candidates = db.query(models.Candidate).all()
        return candidates
    except Exception as e:
        log_error(e, context={"operation": "get_candidates", "admin_id": current_admin.id})
        raise

@router.put("/candidates/{candidate_id}", response_model=schemas.CandidateResponse)
async def update_candidate(
    candidate_id: int,
    payload: schemas.IntakeCandidate,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Update an existing candidate."""
    try:
        candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Parse resume if provided
        resume_data = candidate.resume_json or {"skills": []}
        if payload.resume_url:
            parsed_resume = await resume_parser.parse_resume_from_url(payload.resume_url)
            resume_data = {
                "skills": parsed_resume.get("skills", []),
                "experience": parsed_resume.get("experience", []),
                "education": parsed_resume.get("education", []),
                "text": parsed_resume.get("text", "")
            }
        elif payload.resume_text:
            parsed_resume = await resume_parser.parse_resume_from_text(payload.resume_text)
            resume_data = {
                "skills": parsed_resume.get("skills", []),
                "experience": parsed_resume.get("experience", []),
                "education": parsed_resume.get("education", []),
                "text": parsed_resume.get("text", payload.resume_text)
            }
        
        # Update candidate fields
        candidate.name = payload.name
        candidate.email = payload.email
        candidate.phone = payload.phone
        candidate.resume_url = payload.resume_url
        candidate.resume_json = resume_data
        
        db.commit()
        db.refresh(candidate)
        
        log_business_event("candidate_updated", "candidate", candidate.id,
                          admin_id=current_admin.id, name=payload.name, email=payload.email)
        
        # Invalidate related cache entries
        cache_service.invalidate_related("candidate", candidate.id)
        
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context={"operation": "update_candidate", "admin_id": current_admin.id, "candidate_id": candidate_id})
        raise

@router.delete("/candidates/{candidate_id}")
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Delete a candidate."""
    try:
        candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        db.delete(candidate)
        db.commit()
        
        log_business_event("candidate_deleted", "candidate", candidate_id,
                          admin_id=current_admin.id, name=candidate.name, email=candidate.email)
        
        # Invalidate related cache entries
        cache_service.invalidate_related("candidate", candidate_id)
        
        return {"message": "Candidate deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context={"operation": "delete_candidate", "admin_id": current_admin.id, "candidate_id": candidate_id})
        raise

@router.put("/jobs/{job_id}", response_model=schemas.JobResponse)
def update_job(
    job_id: int,
    payload: schemas.IntakeJob,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Update an existing job."""
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job fields
        job.title = payload.title
        job.jd_text = payload.jd_text
        job.jd_json = {"must_have": payload.must_have, "nice_to_have": payload.nice_to_have}
        
        db.commit()
        db.refresh(job)
        
        log_business_event("job_updated", "job", job.id,
                          admin_id=current_admin.id, title=payload.title)
        
        # Invalidate related cache entries
        cache_service.invalidate_related("job", job.id)
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context={"operation": "update_job", "admin_id": current_admin.id, "job_id": job_id})
        raise

@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Delete a job."""
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        db.delete(job)
        db.commit()
        
        log_business_event("job_deleted", "job", job_id,
                          admin_id=current_admin.id, title=job.title)
        
        # Invalidate related cache entries
        cache_service.invalidate_related("job", job_id)
        
        return {"message": "Job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context={"operation": "delete_job", "admin_id": current_admin.id, "job_id": job_id})
        raise

@router.get("/applications", response_model=List[schemas.ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Get all applications."""
    try:
        applications = db.query(models.Application).all()
        return applications
    except Exception as e:
        log_error(e, context={"operation": "get_applications", "admin_id": current_admin.id})
        raise
