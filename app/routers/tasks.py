from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from ..services.auth import get_current_admin
from .. import models
from ..services.logger import log_business_event
from ..tasks.email_tasks import send_interview_invite_task, send_interview_confirmation_task
from ..tasks.ai_tasks import process_resume_background_task, compute_match_score_background_task
from ..tasks.analytics_tasks import generate_dashboard_stats_task, cleanup_old_data_task
from ..celery_app import celery_app
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class SendInviteRequest(BaseModel):
    application_id: int
    candidate_email: str
    job_title: str
    interview_url: str

class SendConfirmationRequest(BaseModel):
    application_id: int
    candidate_email: str
    job_title: str
    interview_url: str
    start_time: str
    end_time: str

class ProcessResumeRequest(BaseModel):
    candidate_id: int
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None

class ComputeMatchRequest(BaseModel):
    job_id: int
    candidate_id: int

@router.post("/send-invite", response_model=TaskStatusResponse)
def send_invite_background(
    request: SendInviteRequest,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Send interview invitation email in background."""
    try:
        task = send_interview_invite_task.delay(
            request.application_id,
            request.candidate_email,
            request.job_title,
            request.interview_url
        )
        
        log_business_event("task_queued", "email_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="send_invite")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.post("/send-confirmation", response_model=TaskStatusResponse)
def send_confirmation_background(
    request: SendConfirmationRequest,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Send interview confirmation email in background."""
    try:
        task = send_interview_confirmation_task.delay(
            request.application_id,
            request.candidate_email,
            request.job_title,
            request.interview_url,
            request.start_time,
            request.end_time
        )
        
        log_business_event("task_queued", "email_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="send_confirmation")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.post("/process-resume", response_model=TaskStatusResponse)
def process_resume_background(
    request: ProcessResumeRequest,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Process resume in background."""
    try:
        task = process_resume_background_task.delay(
            request.candidate_id,
            request.resume_url,
            request.resume_text
        )
        
        log_business_event("task_queued", "ai_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="process_resume")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.post("/compute-match", response_model=TaskStatusResponse)
def compute_match_background(
    request: ComputeMatchRequest,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Compute match score in background."""
    try:
        task = compute_match_score_background_task.delay(
            request.job_id,
            request.candidate_id
        )
        
        log_business_event("task_queued", "ai_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="compute_match")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.post("/generate-stats", response_model=TaskStatusResponse)
def generate_dashboard_stats_background(
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Generate dashboard statistics in background."""
    try:
        task = generate_dashboard_stats_task.delay()
        
        log_business_event("task_queued", "analytics_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="generate_stats")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.post("/cleanup-data", response_model=TaskStatusResponse)
def cleanup_old_data_background(
    days_to_keep: int = 90,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Clean up old data in background."""
    try:
        task = cleanup_old_data_task.delay(days_to_keep)
        
        log_business_event("task_queued", "analytics_task", None,
                          admin_id=current_admin.id, task_id=task.id, task_type="cleanup_data")
        
        return TaskStatusResponse(
            task_id=task.id,
            status="queued"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    current_admin: models.Admin = Depends(get_current_admin)
):
    """Get the status of a background task."""
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            return TaskStatusResponse(task_id=task_id, status="pending")
        elif task.state == "PROGRESS":
            return TaskStatusResponse(
                task_id=task_id,
                status="progress",
                result=task.info
            )
        elif task.state == "SUCCESS":
            return TaskStatusResponse(
                task_id=task_id,
                status="success",
                result=task.result
            )
        elif task.state == "FAILURE":
            return TaskStatusResponse(
                task_id=task_id,
                status="failure",
                error=str(task.info)
            )
        else:
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state,
                result=task.info
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

@router.get("/active")
def get_active_tasks(current_admin: models.Admin = Depends(get_current_admin)):
    """Get list of active tasks."""
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {"active_tasks": []}
        
        # Flatten the results
        all_active_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_active_tasks.append({
                    "task_id": task["id"],
                    "name": task["name"],
                    "worker": worker,
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {})
                })
        
        return {"active_tasks": all_active_tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {str(e)}")

@router.get("/stats")
def get_task_stats(current_admin: models.Admin = Depends(get_current_admin)):
    """Get task queue statistics."""
    try:
        inspect = celery_app.control.inspect()
        
        # Get various statistics
        stats = {
            "active_tasks": len(inspect.active() or {}),
            "scheduled_tasks": len(inspect.scheduled() or {}),
            "reserved_tasks": len(inspect.reserved() or {}),
            "registered_tasks": list(celery_app.tasks.keys())
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {str(e)}")
