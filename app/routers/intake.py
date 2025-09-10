from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
