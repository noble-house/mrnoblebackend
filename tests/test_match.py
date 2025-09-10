import pytest
from fastapi.testclient import TestClient

def test_match_success(client, auth_headers, sample_job, sample_candidate):
    """Test successful candidate-job matching."""
    match_data = {
        "job_id": sample_job.id,
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "application_id" in data
    assert "fit_score" in data
    assert "fit_status" in data
    assert "reasons" in data
    assert isinstance(data["fit_score"], (int, float))
    assert data["fit_status"] in ["FIT", "BORDERLINE", "NOT_FIT"]

def test_match_job_not_found(client, auth_headers, sample_candidate):
    """Test matching with non-existent job."""
    match_data = {
        "job_id": 99999,  # Non-existent job ID
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert "job or candidate not found" in response.json()["detail"]

def test_match_candidate_not_found(client, auth_headers, sample_job):
    """Test matching with non-existent candidate."""
    match_data = {
        "job_id": sample_job.id,
        "candidate_id": 99999  # Non-existent candidate ID
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert "job or candidate not found" in response.json()["detail"]

def test_match_invalid_job_id(client, auth_headers, sample_candidate):
    """Test matching with invalid job ID."""
    match_data = {
        "job_id": -1,  # Invalid job ID
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_match_invalid_candidate_id(client, auth_headers, sample_job):
    """Test matching with invalid candidate ID."""
    match_data = {
        "job_id": sample_job.id,
        "candidate_id": -1  # Invalid candidate ID
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_match_unauthorized(client, sample_job, sample_candidate):
    """Test matching without authentication."""
    match_data = {
        "job_id": sample_job.id,
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data)
    
    assert response.status_code == 403

def test_match_missing_job_id(client, auth_headers, sample_candidate):
    """Test matching with missing job ID."""
    match_data = {
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_match_missing_candidate_id(client, auth_headers, sample_job):
    """Test matching with missing candidate ID."""
    match_data = {
        "job_id": sample_job.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_match_creates_application_record(client, auth_headers, sample_job, sample_candidate, db_session):
    """Test that matching creates an application record in the database."""
    from app.models import Application
    
    match_data = {
        "job_id": sample_job.id,
        "candidate_id": sample_candidate.id
    }
    
    response = client.post("/match", json=match_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    application_id = data["application_id"]
    
    # Check that the application was created in the database
    application = db_session.query(Application).filter(Application.id == application_id).first()
    assert application is not None
    assert application.candidate_id == sample_candidate.id
    assert application.job_id == sample_job.id
    assert application.fit_score is not None
    assert application.fit_status is not None
    assert application.reasons is not None
