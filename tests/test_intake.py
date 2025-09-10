import pytest
from fastapi.testclient import TestClient

def test_create_job_success(client, auth_headers):
    """Test successful job creation."""
    job_data = {
        "title": "Senior Python Developer",
        "jd_text": "We are looking for a senior Python developer with experience in FastAPI and PostgreSQL.",
        "must_have": ["Python", "FastAPI", "PostgreSQL"],
        "nice_to_have": ["Docker", "AWS", "Redis"]
    }
    
    response = client.post("/intake/job", json=job_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == job_data["title"]
    assert "id" in data
    assert "created_at" in data

def test_create_job_validation_error(client, auth_headers):
    """Test job creation with validation errors."""
    job_data = {
        "title": "",  # Empty title should fail
        "jd_text": "Short",  # Too short description
        "must_have": ["Python"],
        "nice_to_have": []
    }
    
    response = client.post("/intake/job", json=job_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_create_candidate_success(client, auth_headers):
    """Test successful candidate creation."""
    candidate_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "resume_url": "https://example.com/resume.pdf"
    }
    
    response = client.post("/intake/candidate", json=candidate_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == candidate_data["name"]
    assert data["email"] == candidate_data["email"]
    assert "id" in data
    assert "created_at" in data

def test_create_candidate_invalid_email(client, auth_headers):
    """Test candidate creation with invalid email."""
    candidate_data = {
        "name": "John Doe",
        "email": "invalid-email",
        "phone": "+1-555-123-4567"
    }
    
    response = client.post("/intake/candidate", json=candidate_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_create_candidate_invalid_phone(client, auth_headers):
    """Test candidate creation with invalid phone number."""
    candidate_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "invalid-phone"
    }
    
    response = client.post("/intake/candidate", json=candidate_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_create_candidate_invalid_resume_url(client, auth_headers):
    """Test candidate creation with invalid resume URL."""
    candidate_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "resume_url": "not-a-url"
    }
    
    response = client.post("/intake/candidate", json=candidate_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_create_candidate_with_resume_text(client, auth_headers):
    """Test candidate creation with resume text."""
    candidate_data = {
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "resume_text": "Jane Smith\nSoftware Engineer\n5 years experience in Python and React"
    }
    
    response = client.post("/intake/candidate", json=candidate_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == candidate_data["name"]
    assert data["email"] == candidate_data["email"]

def test_create_job_unauthorized(client):
    """Test job creation without authentication."""
    job_data = {
        "title": "Test Job",
        "jd_text": "Test description",
        "must_have": ["Python"],
        "nice_to_have": []
    }
    
    response = client.post("/intake/job", json=job_data)
    
    assert response.status_code == 403

def test_create_candidate_unauthorized(client):
    """Test candidate creation without authentication."""
    candidate_data = {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }
    
    response = client.post("/intake/candidate", json=candidate_data)
    
    assert response.status_code == 403
