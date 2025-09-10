from celery import current_task
from ..celery_app import celery_app
from ..services.logger import log_business_event, log_error, get_logger
from ..db import SessionLocal
from .. import models
from datetime import datetime, timedelta

logger = get_logger("analytics_tasks")

@celery_app.task(bind=True, name="generate_dashboard_stats")
def generate_dashboard_stats_task(self):
    """Generate dashboard statistics in background."""
    try:
        logger.info("Starting dashboard stats generation")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Calculating statistics..."}
        )
        
        db = SessionLocal()
        try:
            # Calculate various statistics
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Counting jobs and candidates..."}
            )
            
            total_jobs = db.query(models.Job).count()
            total_candidates = db.query(models.Candidate).count()
            total_applications = db.query(models.Application).count()
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 40, "total": 100, "status": "Analyzing application statuses..."}
            )
            
            fit_applications = db.query(models.Application).filter(models.Application.fit_status == "FIT").count()
            borderline_applications = db.query(models.Application).filter(models.Application.fit_status == "BORDERLINE").count()
            not_fit_applications = db.query(models.Application).filter(models.Application.fit_status == "NOT_FIT").count()
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 60, "total": 100, "status": "Counting interviews..."}
            )
            
            scheduled_interviews = db.query(models.InterviewLink).filter(
                models.InterviewLink.status == "SCHEDULED"
            ).count()
            
            completed_interviews = db.query(models.Interview).filter(
                models.Interview.status == "COMPLETED"
            ).count()
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Generating recent activity..."}
            )
            
            # Get recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(days=1)
            
            recent_jobs = db.query(models.Job).filter(models.Job.created_at >= recent_cutoff).count()
            recent_candidates = db.query(models.Candidate).filter(models.Candidate.created_at >= recent_cutoff).count()
            recent_applications = db.query(models.Application).filter(models.Application.created_at >= recent_cutoff).count()
            
            stats = {
                "total_jobs": total_jobs,
                "total_candidates": total_candidates,
                "total_applications": total_applications,
                "fit_applications": fit_applications,
                "borderline_applications": borderline_applications,
                "not_fit_applications": not_fit_applications,
                "scheduled_interviews": scheduled_interviews,
                "completed_interviews": completed_interviews,
                "recent_jobs": recent_jobs,
                "recent_candidates": recent_candidates,
                "recent_applications": recent_applications,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            log_business_event("dashboard_stats_generated", "analytics", None, stats=stats)
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Dashboard stats generated successfully"}
        )
        
        logger.info("Dashboard stats generation completed")
        return {"status": "success", "stats": stats}
        
    except Exception as e:
        log_error(e, context={"operation": "generate_dashboard_stats_task"})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="cleanup_old_data")
def cleanup_old_data_task(self, days_to_keep: int = 90):
    """Clean up old data in background."""
    try:
        logger.info(f"Starting data cleanup for data older than {days_to_keep} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting cleanup..."}
        )
        
        db = SessionLocal()
        try:
            # Clean up old email logs
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Cleaning email logs..."}
            )
            
            old_email_logs = db.query(models.EmailLog).filter(models.EmailLog.created_at < cutoff_date)
            email_logs_count = old_email_logs.count()
            old_email_logs.delete(synchronize_session=False)
            
            # Clean up old availability options
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 40, "total": 100, "status": "Cleaning availability options..."}
            )
            
            old_availability = db.query(models.AvailabilityOption).filter(models.AvailabilityOption.created_at < cutoff_date)
            availability_count = old_availability.count()
            old_availability.delete(synchronize_session=False)
            
            # Clean up old interviews
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 60, "total": 100, "status": "Cleaning old interviews..."}
            )
            
            old_interviews = db.query(models.Interview).filter(models.Interview.created_at < cutoff_date)
            interviews_count = old_interviews.count()
            old_interviews.delete(synchronize_session=False)
            
            # Clean up old interview links
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Cleaning old interview links..."}
            )
            
            old_links = db.query(models.InterviewLink).filter(models.InterviewLink.created_at < cutoff_date)
            links_count = old_links.count()
            old_links.delete(synchronize_session=False)
            
            db.commit()
            
            cleanup_stats = {
                "email_logs_deleted": email_logs_count,
                "availability_options_deleted": availability_count,
                "interviews_deleted": interviews_count,
                "interview_links_deleted": links_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
            log_business_event("data_cleanup_completed", "analytics", None, cleanup_stats=cleanup_stats)
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Data cleanup completed successfully"}
        )
        
        logger.info(f"Data cleanup completed. Deleted {email_logs_count + availability_count + interviews_count + links_count} records")
        return {"status": "success", "cleanup_stats": cleanup_stats}
        
    except Exception as e:
        log_error(e, context={"operation": "cleanup_old_data_task", "days_to_keep": days_to_keep})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="generate_weekly_report")
def generate_weekly_report_task(self):
    """Generate weekly analytics report."""
    try:
        logger.info("Starting weekly report generation")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Generating weekly report..."}
        )
        
        db = SessionLocal()
        try:
            # Get date range for last week
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Calculating weekly metrics..."}
            )
            
            # Weekly metrics
            weekly_jobs = db.query(models.Job).filter(
                models.Job.created_at >= start_date,
                models.Job.created_at < end_date
            ).count()
            
            weekly_candidates = db.query(models.Candidate).filter(
                models.Candidate.created_at >= start_date,
                models.Candidate.created_at < end_date
            ).count()
            
            weekly_applications = db.query(models.Application).filter(
                models.Application.created_at >= start_date,
                models.Application.created_at < end_date
            ).count()
            
            weekly_interviews = db.query(models.Interview).filter(
                models.Interview.created_at >= start_date,
                models.Interview.created_at < end_date
            ).count()
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 60, "total": 100, "status": "Analyzing trends..."}
            )
            
            # Calculate trends (compare with previous week)
            prev_start = start_date - timedelta(days=7)
            prev_end = start_date
            
            prev_weekly_jobs = db.query(models.Job).filter(
                models.Job.created_at >= prev_start,
                models.Job.created_at < prev_end
            ).count()
            
            prev_weekly_candidates = db.query(models.Candidate).filter(
                models.Candidate.created_at >= prev_start,
                models.Candidate.created_at < prev_end
            ).count()
            
            # Calculate percentage changes
            jobs_change = ((weekly_jobs - prev_weekly_jobs) / max(prev_weekly_jobs, 1)) * 100
            candidates_change = ((weekly_candidates - prev_weekly_candidates) / max(prev_weekly_candidates, 1)) * 100
            
            report = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "metrics": {
                    "jobs_created": weekly_jobs,
                    "candidates_registered": weekly_candidates,
                    "applications_created": weekly_applications,
                    "interviews_completed": weekly_interviews
                },
                "trends": {
                    "jobs_change_percent": round(jobs_change, 2),
                    "candidates_change_percent": round(candidates_change, 2)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            log_business_event("weekly_report_generated", "analytics", None, report=report)
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Weekly report generated successfully"}
        )
        
        logger.info("Weekly report generation completed")
        return {"status": "success", "report": report}
        
    except Exception as e:
        log_error(e, context={"operation": "generate_weekly_report_task"})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise
