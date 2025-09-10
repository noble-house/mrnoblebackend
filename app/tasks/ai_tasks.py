from celery import current_task
from ..celery_app import celery_app
from ..services.ai_service import ai_service
from ..services.resume_parser import resume_parser
from ..services.logger import log_business_event, log_error, get_logger
from ..db import SessionLocal
from .. import models

logger = get_logger("ai_tasks")

@celery_app.task(bind=True, name="process_resume_background")
def process_resume_background_task(self, candidate_id: int, resume_url: str = None, resume_text: str = None):
    """Process resume in background to extract skills and information."""
    try:
        logger.info(f"Starting resume processing task for candidate {candidate_id}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting resume processing..."}
        )
        
        # Parse resume
        if resume_url:
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Downloading resume..."}
            )
            parsed_data = resume_parser.parse_resume_from_url(resume_url)
        elif resume_text:
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Processing resume text..."}
            )
            parsed_data = resume_parser.parse_resume_from_text(resume_text)
        else:
            raise ValueError("Either resume_url or resume_text must be provided")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 60, "total": 100, "status": "Updating candidate record..."}
        )
        
        # Update candidate record in database
        db = SessionLocal()
        try:
            candidate = db.get(models.Candidate, candidate_id)
            if not candidate:
                raise ValueError(f"Candidate {candidate_id} not found")
            
            # Update resume data
            candidate.resume_json = {
                "skills": parsed_data.get("skills", []),
                "experience": parsed_data.get("experience", []),
                "education": parsed_data.get("education", []),
                "text": parsed_data.get("text", resume_text or "")
            }
            
            db.commit()
            
            log_business_event("resume_processed_background", "candidate", candidate_id,
                             skills_count=len(parsed_data.get("skills", [])),
                             experience_count=len(parsed_data.get("experience", [])))
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Resume processed successfully"}
        )
        
        logger.info(f"Resume processing completed for candidate {candidate_id}")
        return {
            "status": "success",
            "skills_count": len(parsed_data.get("skills", [])),
            "experience_count": len(parsed_data.get("experience", [])),
            "education_count": len(parsed_data.get("education", []))
        }
        
    except Exception as e:
        log_error(e, context={"operation": "process_resume_background_task", "candidate_id": candidate_id})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="compute_match_score_background")
def compute_match_score_background_task(self, job_id: int, candidate_id: int):
    """Compute match score in background."""
    try:
        logger.info(f"Starting match score computation for job {job_id} and candidate {candidate_id}")
        
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Loading data..."}
        )
        
        # Get job and candidate data
        db = SessionLocal()
        try:
            job = db.get(models.Job, job_id)
            candidate = db.get(models.Candidate, candidate_id)
            
            if not job or not candidate:
                raise ValueError("Job or candidate not found")
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 20, "total": 100, "status": "Computing match score..."}
            )
            
            # Compute match score
            job_description = job.jd_text or ""
            job_requirements = job.jd_json or {}
            resume_text = candidate.resume_json.get("text", "") if candidate.resume_json else ""
            resume_skills = candidate.resume_json.get("skills", []) if candidate.resume_json else []
            
            # Use AI service to compute score
            score, status, reasons = ai_service.compute_match_score(
                job_description, job_requirements, resume_text, resume_skills
            )
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 80, "total": 100, "status": "Creating application..."}
            )
            
            # Create application record
            application = models.Application(
                candidate_id=candidate_id,
                job_id=job_id,
                fit_score=score,
                fit_status=models.FitStatus(status),
                reasons=reasons
            )
            db.add(application)
            db.commit()
            db.refresh(application)
            
            log_business_event("match_computed_background", "application", application.id,
                             job_id=job_id, candidate_id=candidate_id, fit_score=score, fit_status=status)
            
        finally:
            db.close()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Match score computed successfully"}
        )
        
        logger.info(f"Match score computation completed for job {job_id} and candidate {candidate_id}")
        return {
            "status": "success",
            "application_id": application.id,
            "fit_score": score,
            "fit_status": status,
            "reasons": reasons
        }
        
    except Exception as e:
        log_error(e, context={"operation": "compute_match_score_background_task", "job_id": job_id, "candidate_id": candidate_id})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Failed: {str(e)}"}
        )
        
        raise

@celery_app.task(bind=True, name="batch_process_candidates")
def batch_process_candidates_task(self, candidate_ids: list):
    """Process multiple candidates in batch."""
    try:
        total_candidates = len(candidate_ids)
        logger.info(f"Starting batch processing for {total_candidates} candidates")
        
        results = []
        
        for i, candidate_id in enumerate(candidate_ids):
            try:
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": i, "total": total_candidates, "status": f"Processing candidate {i+1}/{total_candidates}"}
                )
                
                # Process individual candidate
                db = SessionLocal()
                try:
                    candidate = db.get(models.Candidate, candidate_id)
                    if candidate and candidate.resume_url:
                        # Trigger resume processing
                        process_resume_background_task.delay(candidate_id, resume_url=candidate.resume_url)
                        results.append({"candidate_id": candidate_id, "status": "queued"})
                    else:
                        results.append({"candidate_id": candidate_id, "status": "skipped", "reason": "No resume URL"})
                finally:
                    db.close()
                
            except Exception as e:
                logger.error(f"Failed to process candidate {candidate_id}: {str(e)}")
                results.append({"candidate_id": candidate_id, "status": "failed", "error": str(e)})
        
        current_task.update_state(
            state="SUCCESS",
            meta={"current": total_candidates, "total": total_candidates, "status": "Batch processing completed"}
        )
        
        logger.info(f"Batch processing completed. {len([r for r in results if r['status'] == 'queued'])}/{total_candidates} queued")
        return {"status": "completed", "results": results}
        
    except Exception as e:
        log_error(e, context={"operation": "batch_process_candidates_task"})
        
        current_task.update_state(
            state="FAILURE",
            meta={"current": 0, "total": total_candidates, "status": f"Failed: {str(e)}"}
        )
        
        raise
