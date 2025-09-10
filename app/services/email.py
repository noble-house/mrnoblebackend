import requests, uuid, datetime as dt
from ..config import settings
from .schedule import make_ics
from .logger import log_email_event, log_error

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
HEADERS = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
           "Content-Type": "application/json"}

def send_email(to_email: str, subject: str, body_text: str, ics_bytes: bytes | None = None):
    try:
        data = {
          "personalizations": [{"to": [{"email": to_email}]}],
          "from": {"email": settings.FROM_EMAIL, "name": "Mr Noble"},
          "subject": subject,
          "content": [{"type": "text/plain", "value": body_text}]
        }
        if ics_bytes:
            data["attachments"] = [{
              "content": ics_bytes.decode("utf-8"),
              "filename": "interview.ics",
              "type": "text/calendar"
            }]
        
        r = requests.post(SENDGRID_URL, json=data, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        message_id = r.headers.get("X-Message-Id", str(uuid.uuid4()))
        log_email_event("email_sent", to_email=to_email, subject=subject, message_id=message_id)
        return message_id
        
    except Exception as e:
        log_error(e, context={
            "operation": "send_email",
            "to_email": to_email,
            "subject": subject
        })
        raise

def send_invite(to_email: str, job_title: str, link: str):
    subject = f"You’re shortlisted for {job_title} — share 3 time slots"
    body = (
        f"Hi,\n\nGreat news — you’ve been shortlisted for the {job_title} role.\n"
        "Please REPLY to this email with 3 date & time options (include your timezone).\n"
        "We’ll confirm one and send you the interview link.\n\nThanks,\nTalent Team"
    )
    return send_email(to_email, subject, body)

def send_confirmation(to_email: str, job_title: str, link: str, start: dt.datetime, end: dt.datetime):
    subject = f"Interview confirmed — {job_title}"
    when = start.strftime("%a, %d %b %Y %H:%M")
    body = (
        f"Hi,\n\nYour interview for {job_title} is scheduled on {when} (your timezone).\n"
        f"Join link: {link}\n\nAttachment: calendar invite (.ics)\n"
        "Tip: Use a headset in a quiet room. The interview is recorded for evaluation.\n\nThanks,\nTalent Team"
    )
    ics = make_ics(uid=str(uuid.uuid4()), start=start, end=end, summary=f"Interview — {job_title}", description=f"Join: {link}")
    return send_email(to_email, subject, body, ics_bytes=ics)
