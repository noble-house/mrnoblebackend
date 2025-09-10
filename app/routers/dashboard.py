from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..db import get_db
from .. import models, schemas
from ..services.auth import get_current_admin
from ..services.logger import log_error
from typing import Dict, Any

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
) -> Dict[str, Any]:
    """Get dashboard statistics."""
    try:
        # Count total jobs
        total_jobs = db.query(func.count(models.Job.id)).scalar() or 0
        
        # Count total candidates
        total_candidates = db.query(func.count(models.Candidate.id)).scalar() or 0
        
        # Count total applications
        total_applications = db.query(func.count(models.Application.id)).scalar() or 0
        
        # Count applications by fit status
        fit_applications = db.query(func.count(models.Application.id)).filter(
            models.Application.fit_status == models.FitStatus.FIT
        ).scalar() or 0
        
        borderline_applications = db.query(func.count(models.Application.id)).filter(
            models.Application.fit_status == models.FitStatus.BORDERLINE
        ).scalar() or 0
        
        not_fit_applications = db.query(func.count(models.Application.id)).filter(
            models.Application.fit_status == models.FitStatus.NOT_FIT
        ).scalar() or 0
        
        # Count interview links by status
        scheduled_interviews = db.query(func.count(models.InterviewLink.id)).filter(
            models.InterviewLink.status == models.InterviewStatus.SCHEDULED
        ).scalar() or 0
        
        # Count completed interviews (from Interview table, not InterviewLink)
        completed_interviews = db.query(func.count(models.Interview.id)).filter(
            models.Interview.status == models.RunStatus.COMPLETED
        ).scalar() or 0
        
        return {
            "total_jobs": total_jobs,
            "total_candidates": total_candidates,
            "total_applications": total_applications,
            "fit_applications": fit_applications,
            "borderline_applications": borderline_applications,
            "not_fit_applications": not_fit_applications,
            "scheduled_interviews": scheduled_interviews,
            "completed_interviews": completed_interviews
        }
        
    except Exception as e:
        log_error(e, context={"operation": "get_dashboard_stats", "admin_id": current_admin.id})
        raise

@router.get("/recent-activity")
def get_recent_activity(
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
) -> Dict[str, Any]:
    """Get recent activity for dashboard."""
    try:
        activities = []
        
        # Get recent applications with joins
        recent_applications = db.query(
            models.Application,
            models.Candidate.name.label('candidate_name'),
            models.Job.title.label('job_title')
        ).join(
            models.Candidate, models.Application.candidate_id == models.Candidate.id
        ).join(
            models.Job, models.Application.job_id == models.Job.id
        ).order_by(
            models.Application.created_at.desc()
        ).limit(5).all()
        
        # Add application activities
        for app, candidate_name, job_title in recent_applications:
            activities.append({
                "id": f"app_{app.id}",
                "type": "application",
                "description": f"New application: {candidate_name} for {job_title}",
                "timestamp": app.created_at.isoformat(),
                "status": app.fit_status.value if app.fit_status else None
            })
        
        # Get recent interview links with joins
        recent_interviews = db.query(
            models.InterviewLink,
            models.Candidate.name.label('candidate_name'),
            models.Job.title.label('job_title')
        ).join(
            models.Application, models.InterviewLink.application_id == models.Application.id
        ).join(
            models.Candidate, models.Application.candidate_id == models.Candidate.id
        ).join(
            models.Job, models.Application.job_id == models.Job.id
        ).order_by(
            models.InterviewLink.created_at.desc()
        ).limit(5).all()
        
        # Add interview activities
        for interview, candidate_name, job_title in recent_interviews:
            activities.append({
                "id": f"interview_{interview.id}",
                "type": "interview",
                "description": f"Interview {interview.status.value.lower() if interview.status else 'unknown'}: {candidate_name} for {job_title}",
                "timestamp": interview.created_at.isoformat(),
                "status": interview.status.value if interview.status else None
            })
        
        # Get recent candidates
        recent_candidates = db.query(models.Candidate).order_by(
            models.Candidate.created_at.desc()
        ).limit(5).all()
        
        # Add candidate activities
        for candidate in recent_candidates:
            activities.append({
                "id": f"candidate_{candidate.id}",
                "type": "candidate",
                "description": f"New candidate registered: {candidate.name}",
                "timestamp": candidate.created_at.isoformat()
            })
        
        # Sort by timestamp and return top 10
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return {"activities": activities[:10]}
        
    except Exception as e:
        log_error(e, context={"operation": "get_recent_activity", "admin_id": current_admin.id})
        raise
