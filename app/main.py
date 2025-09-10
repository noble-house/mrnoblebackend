from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from .config import settings
from .db import Base, engine, SessionLocal
from .routers import intake, match, interview, email_inbound, scoring, realtime, auth, cache, tasks, docs
from .services.auth import create_default_admin
from .services.logger import get_logger
from .middleware.logging import LoggingMiddleware
from .exceptions import (
    MrNobleException, BusinessLogicError, DataIntegrityError,
    validation_exception_handler, http_exception_handler, 
    mrnoble_exception_handler, general_exception_handler
)

# Note: In production, use Alembic migrations instead of auto-creating tables
# Run: python migrate.py upgrade
# Base.metadata.create_all(bind=engine)  # Disabled for production

# Create default admin user
db = SessionLocal()
try:
    create_default_admin(db)
finally:
    db.close()

app = FastAPI(
    title="MrNoble API",
    description="""
    ## MrNoble - AI-Powered Interview Automation Platform
    
    A comprehensive API for managing the complete hiring pipeline from job posting to interview completion.
    
    ### Features
    
    * **Authentication**: JWT-based admin authentication
    * **Job Management**: Create and manage job postings
    * **Candidate Management**: Register and manage candidates
    * **AI Matching**: Intelligent candidate-job matching using OpenAI
    * **Resume Parsing**: Automated resume analysis and skill extraction
    * **Interview Scheduling**: Automated interview invitation and scheduling
    * **Email Automation**: SendGrid integration for email communications
    * **Real-time Interviews**: WebRTC integration with OpenAI Realtime API
    * **Analytics**: Comprehensive dashboard and reporting
    * **Background Jobs**: Celery-based task processing
    * **Caching**: Redis-based performance optimization
    
    ### Authentication
    
    Most endpoints require authentication. Use the `/auth/login` endpoint to get a JWT token,
    then include it in the Authorization header: `Bearer <your-token>`
    
    ### Rate Limiting
    
    API calls are rate-limited to prevent abuse. Contact support if you need higher limits.
    
    ### Support
    
    For support, please contact: support@mrnoble.app
    """,
    version="1.0.0",
    contact={
        "name": "MrNoble Support",
        "email": "support@mrnoble.app",
        "url": "https://mrnoble.app/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://api.mrnoble.app",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Admin authentication and authorization"
        },
        {
            "name": "intake",
            "description": "Job and candidate registration"
        },
        {
            "name": "match",
            "description": "AI-powered candidate-job matching"
        },
        {
            "name": "interview",
            "description": "Interview scheduling and management"
        },
        {
            "name": "email",
            "description": "Email processing and automation"
        },
        {
            "name": "scoring",
            "description": "Interview scoring and evaluation"
        },
        {
            "name": "realtime",
            "description": "Real-time interview capabilities"
        },
        {
            "name": "cache",
            "description": "Cache management and monitoring"
        },
        {
            "name": "tasks",
            "description": "Background job management"
        }
    ]
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins or ["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(MrNobleException, mrnoble_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth.router)
app.include_router(intake.router)
app.include_router(match.router)
app.include_router(interview.router)
app.include_router(email_inbound.router)
app.include_router(scoring.router)
app.include_router(realtime.router)
app.include_router(cache.router)
app.include_router(tasks.router)
app.include_router(docs.router)

@app.get("/health")
def health():
    logger = get_logger("health")
    logger.info("Health check requested")
    return {"ok": True}
