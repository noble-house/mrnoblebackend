import pytest
from fastapi.testclient import TestClient

def test_invite_success(client, auth_headers, sample_application):
    """Test successful interview invitation."""
    invite_data = {
        "application_id": sample_application.id
    }
    
    response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "interview_link_id" in data
    assert "token" in data
    assert "candidate_url" in data
    assert "message_id" in data
    assert data["candidate_url"].startswith("http")

def test_invite_application_not_found(client, auth_headers):
    """Test invitation with non-existent application."""
    invite_data = {
        "application_id": 99999
    }
    
    response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert "application not found" in response.json()["detail"]

def test_invite_invalid_application_id(client, auth_headers):
    """Test invitation with invalid application ID."""
    invite_data = {
        "application_id": -1
    }
    
    response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_invite_unauthorized(client, sample_application):
    """Test invitation without authentication."""
    invite_data = {
        "application_id": sample_application.id
    }
    
    response = client.post("/interview/invite", json=invite_data)
    
    assert response.status_code == 403

def test_confirm_success(client, auth_headers, sample_application):
    """Test successful interview confirmation."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    # Now confirm the interview
    confirm_data = {
        "application_id": sample_application.id,
        "slot_iso_start": "2024-01-20T10:00:00Z",
        "slot_iso_end": "2024-01-20T11:00:00Z"
    }
    
    response = client.post("/interview/confirm", json=confirm_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

def test_confirm_invalid_datetime_format(client, auth_headers, sample_application):
    """Test confirmation with invalid datetime format."""
    confirm_data = {
        "application_id": sample_application.id,
        "slot_iso_start": "invalid-datetime",
        "slot_iso_end": "2024-01-20T11:00:00Z"
    }
    
    response = client.post("/interview/confirm", json=confirm_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_confirm_application_not_found(client, auth_headers):
    """Test confirmation with non-existent application."""
    confirm_data = {
        "application_id": 99999,
        "slot_iso_start": "2024-01-20T10:00:00Z",
        "slot_iso_end": "2024-01-20T11:00:00Z"
    }
    
    response = client.post("/interview/confirm", json=confirm_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert "application not found" in response.json()["detail"]

def test_confirm_unauthorized(client, sample_application):
    """Test confirmation without authentication."""
    confirm_data = {
        "application_id": sample_application.id,
        "slot_iso_start": "2024-01-20T10:00:00Z",
        "slot_iso_end": "2024-01-20T11:00:00Z"
    }
    
    response = client.post("/interview/confirm", json=confirm_data)
    
    assert response.status_code == 403

def test_join_valid_token(client, sample_application, auth_headers):
    """Test joining interview with valid token."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    # Now try to join the interview
    response = client.get(f"/interview/join/{token}")
    
    assert response.status_code == 200
    data = response.json()
    assert "application_id" in data
    assert "candidate_name" in data
    assert "job_title" in data
    assert "status" in data

def test_join_invalid_token(client):
    """Test joining interview with invalid token."""
    response = client.get("/interview/join/invalid-token")
    
    assert response.status_code == 404
    assert "invalid token" in response.json()["detail"]

def test_join_nonexistent_token(client):
    """Test joining interview with non-existent token."""
    response = client.get("/interview/join/nonexistent-token-12345")
    
    assert response.status_code == 404
    assert "invalid token" in response.json()["detail"]
