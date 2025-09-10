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
            models.Application.fit_status == "FIT"
        ).scalar() or 0
        
        borderline_applications = db.query(func.count(models.Application.id)).filter(
            models.Application.fit_status == "BORDERLINE"
        ).scalar() or 0
        
        not_fit_applications = db.query(func.count(models.Application.id)).filter(
            models.Application.fit_status == "NOT_FIT"
        ).scalar() or 0
        
        # Count interview links by status
        scheduled_interviews = db.query(func.count(models.InterviewLink.id)).filter(
            models.InterviewLink.status == "SCHEDULED"
        ).scalar() or 0
        
        completed_interviews = db.query(func.count(models.InterviewLink.id)).filter(
            models.InterviewLink.status == "COMPLETED"
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
        # Get recent applications
        recent_applications = db.query(models.Application).order_by(
            models.Application.created_at.desc()
        ).limit(5).all()
        
        # Get recent interview links
        recent_interviews = db.query(models.InterviewLink).order_by(
            models.InterviewLink.created_at.desc()
        ).limit(5).all()
        
        # Get recent candidates
        recent_candidates = db.query(models.Candidate).order_by(
            models.Candidate.created_at.desc()
        ).limit(5).all()
        
        activities = []
        
        # Add application activities
        for app in recent_applications:
            activities.append({
                "id": f"app_{app.id}",
                "type": "application",
                "description": f"New application: {app.candidate.name} for {app.job.title}",
                "timestamp": app.created_at.isoformat(),
                "status": app.fit_status.value if app.fit_status else None
            })
        
        # Add interview activities
        for interview in recent_interviews:
            activities.append({
                "id": f"interview_{interview.id}",
                "type": "interview",
                "description": f"Interview {interview.status.value.lower()}: {interview.application.candidate.name} for {interview.application.job.title}",
                "timestamp": interview.created_at.isoformat(),
                "status": interview.status.value
            })
        
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
