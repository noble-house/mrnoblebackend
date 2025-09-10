from celery import current_task
from ..celery_app import celery_app
from ..services.email import send_email, send_invite, send_confirmation
from ..services.logger import log_business_event, log_error, get_logger
from ..db import SessionLocal
from .. import models
from datetime import datetime

logger = get_logger("email_tasks")

@celery_app.task(bind=True, name="send_interview_invite")
def send_interview_invite_task(self, application_id: int, candidate_email: str, job_title: str, interview_url: str):
    """Send interview invitation email in background."""
    try:
        logger.info(f"Starting interview invite task for application {application_id}")
        
        # Update task status
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Sending email..."}
        )
        
        # Send the email
        message_id = send_invite(candidate_email, job_title, interview_url)
        
        # Update task status
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Email sent, logging..."}
        )
        
        # Log the email in database
        db = SessionLocal()
        try:
            email_log = models.EmailLog(
                application_id=application_id,
                type="INVITE",
                to_email=candidate_email,
                subject=f"You're shortlisted for {job_title} — share 3 time slots",
                body=f"Interview link: {interview_url}",
                provider_message_id=message_id
            )
            db.add(email_log)
            db.commit()
            
            log_business_event("email_sent_background", "email_log", email_log.id,
                             application_id=application_id, message_id=message_id)
            
        finally:
            db.close()
        
        # Complete task
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Email sent successfully", "message_id": message_id}
        )
        
        logger.info(f"Interview invite sent successfully for application {application_id}")
        return {"status": "success", "message_id": message_id}
        
    except Exception as e:
        log_error(e, context={"operation": "send_interview_invite_task", "application_id": application_id})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="send_interview_confirmation")
def send_interview_confirmation_task(self, application_id: int, candidate_email: str, job_title: str, 
                                   interview_url: str, start_time: str, end_time: str):
    """Send interview confirmation email in background."""
    try:
        logger.info(f"Starting interview confirmation task for application {application_id}")
        
        # Parse datetime strings
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Sending confirmation email..."}
        )
        
        # Send the email
        message_id = send_confirmation(candidate_email, job_title, interview_url, start_dt, end_dt)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Email sent, logging..."}
        )
        
        # Log the email in database
        db = SessionLocal()
        try:
            email_log = models.EmailLog(
                application_id=application_id,
                type="CONFIRMATION",
                to_email=candidate_email,
                subject=f"Interview confirmed — {job_title}",
                body=f"Interview scheduled: {start_time} to {end_time}. Link: {interview_url}",
                provider_message_id=message_id
            )
            db.add(email_log)
            db.commit()
            
            log_business_event("email_sent_background", "email_log", email_log.id,
                             application_id=application_id, message_id=message_id, type="CONFIRMATION")
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Confirmation sent successfully", "message_id": message_id}
        )
        
        logger.info(f"Interview confirmation sent successfully for application {application_id}")
        return {"status": "success", "message_id": message_id}
        
    except Exception as e:
        log_error(e, context={"operation": "send_interview_confirmation_task", "application_id": application_id})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="send_bulk_emails")
def send_bulk_emails_task(self, email_data: list):
    """Send multiple emails in background."""
    try:
        total_emails = len(email_data)
        logger.info(f"Starting bulk email task for {total_emails} emails")
        
        results = []
        
        for i, email_info in enumerate(email_data):
            try:
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": i, "total": total_emails, "status": f"Sending email {i+1}/{total_emails}"}
                )
                
                # Send individual email
                message_id = send_email(
                    email_info["to_email"],
                    email_info["subject"],
                    email_info["body"]
                )
                
                results.append({
                    "to_email": email_info["to_email"],
                    "status": "success",
                    "message_id": message_id
                })
                
            except Exception as e:
                logger.error(f"Failed to send email to {email_info.get('to_email', 'unknown')}: {str(e)}")
                results.append({
                    "to_email": email_info.get("to_email", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": total_emails, "total": total_emails, "status": "Bulk emails completed"}
        )
        
        logger.info(f"Bulk email task completed. {len([r for r in results if r['status'] == 'success'])}/{total_emails} successful")
        return {"status": "completed", "results": results}
        
    except Exception as e:
        log_error(e, context={"operation": "send_bulk_emails_task"})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": total_emails, "status": f"Failed: {str(e)}"}
        )
        
        raise
