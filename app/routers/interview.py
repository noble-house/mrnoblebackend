import secrets, datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.email import send_invite, send_confirmation
from ..services.auth import get_current_admin
from ..config import settings

router = APIRouter(prefix="/interview", tags=["interview"])

@router.post("/invite")
def invite(
    req: schemas.InviteRequest, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    app = db.get(models.Application, req.application_id)
    if not app: raise HTTPException(404, "application not found")
    token = secrets.token_urlsafe(24)
    link = models.InterviewLink(application_id=app.id, token=token, status=models.InterviewStatus.NEW)
    db.add(link); db.commit(); db.refresh(link)
    url = f"{settings.APP_BASE_URL}/i/{token}"
    msg_id = send_invite(app.candidate.email, app.job.title, url)
    return {"interview_link_id": link.id, "token": token, "candidate_url": url, "message_id": msg_id}

@router.post("/confirm")
def confirm(
    req: schemas.ConfirmRequest, 
    db: Session = Depends(get_db),
    current_admin: models.Admin = Depends(get_current_admin)
):
    app = db.get(models.Application, req.application_id)
    if not app: raise HTTPException(404, "application not found")
    link = db.query(models.InterviewLink).filter_by(application_id=app.id).order_by(models.InterviewLink.id.desc()).first()
    if not link: raise HTTPException(400, "no link for application")
    start = dt.datetime.fromisoformat(req.slot_iso_start)
    end = dt.datetime.fromisoformat(req.slot_iso_end)
    link.scheduled_start_at, link.scheduled_end_at, link.status = start, end, models.InterviewStatus.SCHEDULED
    db.commit()
    url = f"{settings.APP_BASE_URL}/i/{link.token}"
    send_confirmation(app.candidate.email, app.job.title, url, start=start, end=end)
    return {"ok": True}

@router.get("/join/{token}")
def join(token: str, db: Session = Depends(get_db)):
    link = db.query(models.InterviewLink).filter_by(token=token).first()
    if not link: raise HTTPException(404, "invalid token")
    
    # Generate WebRTC credentials for the interview session
    from ..services.realtime import generate_webrtc_credentials
    webrtc_creds = generate_webrtc_credentials(link.id, link.application_id)
    
    return {
        "status": link.status.value, 
        "scheduled_start_at": link.scheduled_start_at, 
        "webrtc": webrtc_creds
    }
