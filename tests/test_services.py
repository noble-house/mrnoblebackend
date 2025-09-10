import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from ..services.auth import verify_password, get_password_hash, create_access_token, verify_token, authenticate_admin
from ..services.cache import CacheService
from ..services.ai_service import AIService
from ..services.email import send_email
from ..services.parse_reply import EmailParser
from ..services.resume_parser import ResumeParser
from .. import models

class TestAuthService:
    """Test authentication service functions."""
    
    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT tokens have 3 parts separated by dots
        assert len(token.split(".")) == 3
    
    def test_verify_token_success(self):
        """Test successful token verification."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        verified_data = verify_token(token)
        assert verified_data is not None
        assert verified_data["sub"] == "test@example.com"
    
    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        invalid_token = "invalid.token.here"
        
        verified_data = verify_token(invalid_token)
        assert verified_data is None
    
    def test_authenticate_admin_success(self, db_session, admin_user):
        """Test successful admin authentication."""
        admin = authenticate_admin(db_session, admin_user.email, "admin123")
        
        assert admin is not None
        assert admin.email == admin_user.email
        assert admin.id == admin_user.id
    
    def test_authenticate_admin_wrong_password(self, db_session, admin_user):
        """Test admin authentication with wrong password."""
        admin = authenticate_admin(db_session, admin_user.email, "wrong_password")
        
        assert admin is None
    
    def test_authenticate_admin_nonexistent_user(self, db_session):
        """Test admin authentication with non-existent user."""
        admin = authenticate_admin(db_session, "nonexistent@example.com", "password")
        
        assert admin is None

class TestCacheService:
    """Test cache service functionality."""
    
    def test_cache_service_initialization(self):
        """Test cache service initialization."""
        cache = CacheService()
        assert cache is not None
    
    @patch('redis.Redis')
    def test_cache_set_get(self, mock_redis):
        """Test cache set and get operations."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheService()
        
        # Test set
        cache.set("test_key", "test_value", ttl=3600)
        mock_redis_instance.setex.assert_called_once_with("test_key", 3600, "test_value")
        
        # Test get
        mock_redis_instance.get.return_value = "test_value"
        result = cache.get("test_key")
        assert result == "test_value"
        mock_redis_instance.get.assert_called_once_with("test_key")
    
    @patch('redis.Redis')
    def test_cache_delete(self, mock_redis):
        """Test cache delete operation."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheService()
        cache.delete("test_key")
        
        mock_redis_instance.delete.assert_called_once_with("test_key")
    
    @patch('redis.Redis')
    def test_cache_clear_all(self, mock_redis):
        """Test cache clear all operation."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        
        cache = CacheService()
        cache.clear_all()
        
        mock_redis_instance.flushdb.assert_called_once()
    
    @patch('redis.Redis')
    def test_cache_ping(self, mock_redis):
        """Test cache ping operation."""
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        
        cache = CacheService()
        result = cache.ping()
        
        assert result is True
        mock_redis_instance.ping.assert_called_once()

class TestAIService:
    """Test AI service functionality."""
    
    def test_ai_service_initialization(self):
        """Test AI service initialization."""
        ai_service = AIService()
        assert ai_service is not None
        assert ai_service.embedding_model == "text-embedding-ada-002"
        assert ai_service.chat_model == "gpt-3.5-turbo"
    
    @patch('openai.Embedding.acreate')
    async def test_get_embedding_success(self, mock_embedding):
        """Test successful embedding retrieval."""
        mock_embedding.return_value = {
            'data': [{'embedding': [0.1, 0.2, 0.3, 0.4, 0.5]}]
        }
        
        ai_service = AIService()
        result = await ai_service.get_embedding("test text")
        
        assert result == [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_embedding.assert_called_once()
    
    @patch('openai.Embedding.acreate')
    async def test_get_embedding_failure(self, mock_embedding):
        """Test embedding retrieval failure."""
        mock_embedding.side_effect = Exception("API Error")
        
        ai_service = AIService()
        result = await ai_service.get_embedding("test text")
        
        assert result is None
    
    async def test_get_embedding_empty_text(self):
        """Test embedding retrieval with empty text."""
        ai_service = AIService()
        result = await ai_service.get_embedding("")
        
        assert result is None
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        ai_service = AIService()
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        # Orthogonal vectors should have similarity close to 0
        similarity1 = ai_service.calculate_similarity(vec1, vec2)
        assert abs(similarity1) < 0.1
        
        # Identical vectors should have similarity close to 1
        similarity2 = ai_service.calculate_similarity(vec1, vec3)
        assert abs(similarity2 - 1.0) < 0.1
    
    @patch('openai.ChatCompletion.acreate')
    async def test_extract_skills_from_text(self, mock_chat):
        """Test skill extraction from text."""
        mock_chat.return_value = {
            'choices': [{
                'message': {
                    'content': '["Python", "JavaScript", "React", "Node.js"]'
                }
            }]
        }
        
        ai_service = AIService()
        result = await ai_service.extract_skills_from_text("I have experience with Python, JavaScript, React, and Node.js")
        
        assert result == ["Python", "JavaScript", "React", "Node.js"]
        mock_chat.assert_called_once()
    
    @patch('openai.ChatCompletion.acreate')
    async def test_analyze_job_requirements(self, mock_chat):
        """Test job requirements analysis."""
        mock_chat.return_value = {
            'choices': [{
                'message': {
                    'content': '{"must_have": ["Python", "FastAPI"], "nice_to_have": ["Docker", "AWS"], "experience_level": "Senior"}'
                }
            }]
        }
        
        ai_service = AIService()
        result = await ai_service.analyze_job_requirements("We need a senior Python developer with FastAPI experience")
        
        assert "must_have" in result
        assert "nice_to_have" in result
        assert "experience_level" in result
        assert "Python" in result["must_have"]
        assert "FastAPI" in result["must_have"]

class TestEmailService:
    """Test email service functionality."""
    
    @patch('sendgrid.SendGridAPIClient')
    def test_send_email_success(self, mock_sendgrid):
        """Test successful email sending."""
        mock_client = Mock()
        mock_sendgrid.return_value = mock_client
        mock_client.send.return_value = Mock(status_code=202)
        
        result = send_email("test@example.com", "Test Subject", "Test Body")
        
        assert result is True
        mock_client.send.assert_called_once()
    
    @patch('sendgrid.SendGridAPIClient')
    def test_send_email_failure(self, mock_sendgrid):
        """Test email sending failure."""
        mock_client = Mock()
        mock_sendgrid.return_value = mock_client
        mock_client.send.side_effect = Exception("SendGrid Error")
        
        result = send_email("test@example.com", "Test Subject", "Test Body")
        
        assert result is False

class TestEmailParser:
    """Test email parser functionality."""
    
    def test_email_parser_initialization(self):
        """Test email parser initialization."""
        parser = EmailParser()
        assert parser is not None
        assert len(parser.time_patterns) > 0
    
    def test_clean_and_normalize_text(self):
        """Test text cleaning and normalization."""
        parser = EmailParser()
        
        dirty_text = "  <p>Hello   world</p>  \n\n  Best regards,  \n  John  "
        clean_text = parser.clean_and_normalize_text(dirty_text)
        
        assert "Hello world" in clean_text
        assert "<p>" not in clean_text
        assert "Best regards" not in clean_text
        assert clean_text.strip() == clean_text
    
    def test_validate_slot_format_valid(self):
        """Test valid slot format validation."""
        parser = EmailParser()
        
        valid_slot = {
            "start": "2024-01-20T10:00:00Z",
            "end": "2024-01-20T11:00:00Z",
            "description": "Available slot"
        }
        
        assert parser.validate_slot_format(valid_slot) is True
    
    def test_validate_slot_format_invalid(self):
        """Test invalid slot format validation."""
        parser = EmailParser()
        
        invalid_slot = {
            "start": "invalid-datetime",
            "end": "2024-01-20T11:00:00Z"
        }
        
        assert parser.validate_slot_format(invalid_slot) is False
    
    def test_validate_slot_format_missing_fields(self):
        """Test slot format validation with missing fields."""
        parser = EmailParser()
        
        incomplete_slot = {
            "start": "2024-01-20T10:00:00Z"
            # Missing 'end' field
        }
        
        assert parser.validate_slot_format(incomplete_slot) is False

class TestResumeParser:
    """Test resume parser functionality."""
    
    def test_resume_parser_initialization(self):
        """Test resume parser initialization."""
        parser = ResumeParser()
        assert parser is not None
    
    @patch('requests.get')
    @patch('PyPDF2.PdfReader')
    async def test_parse_resume_from_url_success(self, mock_pdf_reader, mock_requests):
        """Test successful resume parsing from URL."""
        # Mock requests response
        mock_response = Mock()
        mock_response.content = b"PDF content"
        mock_requests.return_value = mock_response
        
        # Mock PDF reader
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\nPython, JavaScript, React"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        parser = ResumeParser()
        result = await parser.parse_resume_from_url("http://example.com/resume.pdf")
        
        assert result is not None
        assert "name" in result
        assert "skills" in result
        assert "experience" in result
    
    @patch('requests.get')
    async def test_parse_resume_from_url_failure(self, mock_requests):
        """Test resume parsing from URL failure."""
        mock_requests.side_effect = Exception("Network Error")
        
        parser = ResumeParser()
        result = await parser.parse_resume_from_url("http://example.com/resume.pdf")
        
        assert result is None
    
    async def test_parse_resume_from_text_success(self):
        """Test successful resume parsing from text."""
        resume_text = """
        John Doe
        Software Engineer
        
        Skills: Python, JavaScript, React, Node.js
        Experience: 5 years in software development
        Education: Computer Science Degree
        """
        
        parser = ResumeParser()
        result = await parser.parse_resume_from_text(resume_text)
        
        assert result is not None
        assert "name" in result
        assert "skills" in result
        assert "experience" in result
        assert "education" in result
    
    async def test_parse_resume_from_text_empty(self):
        """Test resume parsing from empty text."""
        parser = ResumeParser()
        result = await parser.parse_resume_from_text("")
        
        assert result is None
