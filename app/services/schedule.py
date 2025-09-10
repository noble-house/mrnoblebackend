from datetime import datetime

def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%SZ")  # UTC basic format

def make_ics(uid: str, start: datetime, end: datetime, summary: str, description: str) -> bytes:
    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MrNoble//Interview//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{_fmt(datetime.utcnow())}
DTSTART:{_fmt(start)}
DTEND:{_fmt(end)}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:Online
END:VEVENT
END:VCALENDAR"""
    return ics.encode("utf-8")
