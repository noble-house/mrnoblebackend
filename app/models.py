from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .db import Base

class FitStatus(str, enum.Enum):
    NOT_FIT = "NOT_FIT"
    FIT = "FIT"
    BORDERLINE = "BORDERLINE"

class InterviewStatus(str, enum.Enum):
    NEW = "NEW"
    SCHEDULED = "SCHEDULED"
    EXPIRED = "EXPIRED"

class RunStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200), index=True)
    phone = Column(String(50))
    resume_url = Column(Text)
    resume_json = Column(JSON)
    resume_embed = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    jd_text = Column(Text)
    jd_json = Column(JSON)
    jd_embed = Column(JSON)
    must_have = Column(JSON)   # list[str]
    nice_to_have = Column(JSON) # list[str]
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    fit_score = Column(Float)
    fit_status = Column(Enum(FitStatus))
    reasons = Column(JSON)  # list[str]
    created_at = Column(DateTime, default=datetime.utcnow)
    candidate = relationship("Candidate")
    job = relationship("Job")

class InterviewLink(Base):
    __tablename__ = "interview_links"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    token = Column(String(64), unique=True, index=True)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.NEW)
    scheduled_start_at = Column(DateTime, nullable=True)
    scheduled_end_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    application = relationship("Application")

class EmailLog(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    type = Column(String(40))  # INVITE / CONFIRMATION / NOTFIT
    to_email = Column(String(200))
    subject = Column(Text)
    body = Column(Text)
    provider_message_id = Column(String(128))
    sent_at = Column(DateTime, default=datetime.utcnow)

class AvailabilityOption(Base):
    __tablename__ = "availability_options"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    raw_email_text = Column(Text)
    parsed_slots = Column(JSON)   # list[{start, end, tz}]
    chosen_slot = Column(JSON)    # single chosen slot dict
    parsed_at = Column(DateTime, default=datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    audio_url = Column(Text)
    transcript_url = Column(Text)
    status = Column(Enum(RunStatus), default=RunStatus.COMPLETED)

class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    rubric = Column(JSON)   # per-dimension numbers
    total_score = Column(Float)
    recommendation = Column(String(20)) # SELECT / REJECT
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
