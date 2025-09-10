# MrNoble Backend

The backend API for MrNoble - AI-Powered Interview Automation Platform.

## 🚀 Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt
- **Background Tasks**: Celery with Redis
- **AI Integration**: OpenAI API
- **Email**: SendGrid
- **Documentation**: Auto-generated OpenAPI/Swagger

## 📋 Features

- **Authentication**: JWT-based admin authentication
- **Job Management**: CRUD operations for job postings
- **Candidate Management**: Registration and resume processing
- **AI Matching**: Intelligent candidate-job matching using OpenAI
- **Resume Parsing**: PDF/DOC text extraction and analysis
- **Interview Scheduling**: Automated interview invitations
- **Email Automation**: SendGrid integration for notifications
- **Real-time Interviews**: WebRTC credential generation
- **Scoring System**: Comprehensive interview evaluation
- **Background Jobs**: Celery-based task processing
- **Caching**: Redis-based performance optimization

## 🛠️ Development

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis (optional, for caching and background tasks)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp env.example .env

# Edit .env with your configuration
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `SENDGRID_API_KEY` | SendGrid API key for emails | Yes | - |
| `FROM_EMAIL` | Sender email address | No | talent@mrnoble.app |
| `APP_BASE_URL` | Frontend application URL | Yes | - |
| `CORS_ORIGINS` | Allowed CORS origins | Yes | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `ADMIN_EMAIL` | Default admin email | No | admin@mrnoble.app |
| `ADMIN_PASSWORD` | Default admin password | No | admin123 |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `REDIS_URL` | Redis connection string | No | redis://localhost:6379/0 |

### Database Setup

```bash
# Run migrations
python migrate.py upgrade

# Create initial migration (if needed)
python migrate.py create "Initial migration"
```

### Running Locally

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With background worker (in separate terminal)
celery -A app.celery_app worker --loglevel=info

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## 🌐 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚀 Deployment

This backend is configured for deployment on **Railway**.

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Set the root directory to `backend`
3. Add PostgreSQL database service
4. Configure environment variables
5. Deploy!

### Health Check

The API provides a health check endpoint:
```
GET /health
```

## 📁 Project Structure

```
backend/
├── app/                    # Main application code
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic services
│   ├── tasks/             # Celery background tasks
│   ├── middleware/        # Custom middleware
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── config.py          # Configuration
│   ├── db.py              # Database setup
│   ├── main.py            # FastAPI application
│   └── exceptions.py      # Custom exceptions
├── alembic/               # Database migrations
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── railway.json          # Railway configuration
├── start.sh              # Startup script
└── migrate.py            # Migration helper
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run tests with specific markers
python -m pytest tests/ -m "not slow" -v
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `GET /auth/me` - Get current admin info

### Job Management
- `POST /intake/job` - Create job posting
- `GET /intake/jobs` - List job postings
- `GET /intake/job/{id}` - Get job details

### Candidate Management
- `POST /intake/candidate` - Register candidate
- `GET /intake/candidates` - List candidates
- `GET /intake/candidate/{id}` - Get candidate details

### Matching & Applications
- `POST /match` - Match candidate to job
- `GET /match/applications` - List applications
- `GET /match/application/{id}` - Get application details

### Interview Management
- `POST /interview/invite` - Send interview invitation
- `POST /interview/confirm` - Confirm interview schedule
- `GET /interview/join/{token}` - Get interview credentials

### Scoring
- `POST /score/{interview_id}/finalize` - Finalize interview scores

### Background Tasks
- `POST /tasks/send-invite` - Send email invitation
- `GET /tasks/status/{task_id}` - Get task status

### Real-time
- `POST /rt/ephemeral` - Generate WebRTC credentials

## 🔐 Security

- JWT token-based authentication
- Password hashing with bcrypt
- CORS protection
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- Rate limiting (configurable)

## 📊 Monitoring

- Structured logging with structlog
- Health check endpoint
- Error tracking and reporting
- Performance metrics

## 🚀 Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Admin credentials changed
- [ ] API keys configured
- [ ] CORS settings updated
- [ ] Health checks passing
- [ ] Background workers running
- [ ] Logging configured
- [ ] Monitoring set up

## 📞 Support

For issues or questions:
1. Check the logs in Railway dashboard
2. Verify environment variables are set correctly
3. Ensure database is accessible
4. Check API documentation at `/docs`

## 🔄 Background Tasks

The application uses Celery for background processing:

- Email sending
- Resume parsing
- AI matching
- Analytics processing

To run background workers:
```bash
celery -A app.celery_app worker --loglevel=info
```