from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models
from ..services.parse_reply import email_parser
from ..services.email import send_confirmation
from ..services.logger import log_business_event, log_error
from ..config import settings
from datetime import datetime

router = APIRouter(prefix="/email", tags=["email"])

@router.post("/inbound")
async def inbound(req: Request, db: Session = Depends(get_db)):
    try:
        data = await req.form()
        to_email = data.get("to")
        subject = data.get("subject", "")
        text = data.get("text", "") or data.get("html", "")
        
        # Clean and normalize the email text
        cleaned_text = email_parser.clean_and_normalize_text(text)
        
        # Strategy: look up application by 'to' alias or thread id if you set one
        # For demo, assume subject contains "AppID:{id}"
        app_id = None
        if "AppID:" in subject:
            try:
                app_id = int(subject.split("AppID:")[1].split()[0])
            except Exception:
                pass
        
        if not app_id:
            log_business_event("email_received", "email", None, 
                             to_email=to_email, subject=subject, note="no application id found")
            return {"ok": True, "note": "no application id found"}

        app = db.get(models.Application, app_id)
        if not app:
            log_business_event("email_received", "email", None, 
                             to_email=to_email, subject=subject, note="application not found")
            return {"ok": True, "note": "application not found"}

        # Extract time slots using enhanced parser
        slots = await email_parser.extract_slots_from_text(cleaned_text)
        
        # Validate slots
        valid_slots = [slot for slot in slots if email_parser.validate_slot_format(slot)]
        
        chosen = valid_slots[0] if valid_slots else None
        
        # Store the availability option
        opt = models.AvailabilityOption(
            application_id=app.id, 
            raw_email_text=text, 
            parsed_slots=valid_slots, 
            chosen_slot=chosen
        )
        db.add(opt)
        db.commit()
        
        log_business_event("availability_parsed", "availability_option", opt.id,
                          application_id=app.id, slots_found=len(valid_slots), auto_scheduled=bool(chosen))
        
        if chosen:
            # Auto-confirm earliest valid slot
            try:
                start = datetime.fromisoformat(chosen["start"].replace('Z', '+00:00'))
                end = datetime.fromisoformat(chosen["end"].replace('Z', '+00:00'))
                
                link = db.query(models.InterviewLink).filter_by(application_id=app.id).order_by(models.InterviewLink.id.desc()).first()
                if link:
                    link.scheduled_start_at = start
                    link.scheduled_end_at = end
                    link.status = models.InterviewStatus.SCHEDULED
                    db.commit()
                    
                    url = f"{settings.APP_BASE_URL}/i/{link.token}"
                    send_confirmation(app.candidate.email, app.job.title, url, start, end)
                    
                    log_business_event("interview_scheduled", "interview_link", link.id,
                                      application_id=app.id, scheduled_start=start.isoformat())
            except Exception as e:
                log_error(e, context={"operation": "schedule_interview", "application_id": app.id})
        
        return {"ok": True, "slots_found": len(valid_slots), "auto_scheduled": bool(chosen)}
        
    except Exception as e:
        log_error(e, context={"operation": "email_inbound", "to_email": to_email, "subject": subject})
        return {"ok": False, "error": "Failed to process email"}
