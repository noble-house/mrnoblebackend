import pytest
from fastapi.testclient import TestClient

def test_process_email_success(client, sample_application, auth_headers):
    """Test successful email processing."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    # Process email with availability
    email_data = {
        "token": token,
        "text": "I'm available on Monday 10:00 AM to 11:00 AM and Tuesday 2:00 PM to 3:00 PM"
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "slots" in data
    assert len(data["slots"]) > 0

def test_process_email_invalid_token(client):
    """Test email processing with invalid token."""
    email_data = {
        "token": "invalid-token",
        "text": "I'm available on Monday 10:00 AM"
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 404
    assert "invalid token" in response.json()["detail"]

def test_process_email_empty_text(client, sample_application, auth_headers):
    """Test email processing with empty text."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    email_data = {
        "token": token,
        "text": ""
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 422

def test_process_email_no_availability(client, sample_application, auth_headers):
    """Test email processing with no availability mentioned."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    email_data = {
        "token": token,
        "text": "Thank you for the invitation. I'll get back to you soon."
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "slots" in data
    assert len(data["slots"]) == 0

def test_process_email_missing_token(client):
    """Test email processing without token."""
    email_data = {
        "text": "I'm available on Monday 10:00 AM"
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 422

def test_process_email_missing_text(client, sample_application, auth_headers):
    """Test email processing without text."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    email_data = {
        "token": token
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 422

def test_process_email_with_multiple_slots(client, sample_application, auth_headers):
    """Test email processing with multiple time slots."""
    # First create an interview link
    invite_data = {"application_id": sample_application.id}
    invite_response = client.post("/interview/invite", json=invite_data, headers=auth_headers)
    assert invite_response.status_code == 200
    
    token = invite_response.json()["token"]
    
    email_data = {
        "token": token,
        "text": """
        Hi, I'm available at the following times:
        1. Monday, January 20th at 10:00 AM
        2. Tuesday, January 21st at 2:00 PM
        3. Wednesday, January 22nd at 3:30 PM
        Please let me know which works best.
        """
    }
    
    response = client.post("/email/process", json=email_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "slots" in data
    assert len(data["slots"]) >= 1  # Should extract at least one slot
