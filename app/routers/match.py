from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.match import compute_fit_score_async
from ..services.auth import get_current_admin
from ..services.logger import log_business_event, log_error

router = APIRouter(prefix="/match", tags=["match"])

@router.post("")
async def match(
    req: schemas.MatchRequest, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    try:
        job = db.get(models.Job, req.job_id)
        cand = db.get(models.Candidate, req.candidate_id)
        if not job or not cand:
            raise HTTPException(404, "job or candidate not found")
        
        # Use AI-powered matching
        job_description = job.jd_text or ""
        job_requirements = job.jd_json or {}
        resume_text = cand.resume_json.get("text", "") if cand.resume_json else ""
        resume_skills = cand.resume_json.get("skills", []) if cand.resume_json else []
        
        score, status, reasons = await compute_fit_score_async(
            job_description, job_requirements, resume_text, resume_skills
        )
        
        app = models.Application(candidate_id=cand.id, job_id=job.id, fit_score=score,
                                 fit_status=models.FitStatus(status), reasons=reasons)
        db.add(app); db.commit(); db.refresh(app)
        
        log_business_event("application_created", "application", app.id,
                          admin_id=current_admin.id, job_id=req.job_id, candidate_id=req.candidate_id,
                          fit_score=score, fit_status=status, ai_powered=True)
        return {"application_id": app.id, "fit_score": score, "fit_status": status, "reasons": reasons}
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, context={"operation": "match", "admin_id": current_admin.id, 
                             "job_id": req.job_id, "candidate_id": req.candidate_id})
        raise
