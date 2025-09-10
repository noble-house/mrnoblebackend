import pytest
from fastapi.testclient import TestClient

def test_send_test_email_success(client, auth_headers):
    """Test successful test email task initiation."""
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "PENDING"
    assert len(data["task_id"]) > 0

def test_send_test_email_invalid_email(client, auth_headers):
    """Test test email task with invalid email format."""
    task_data = {
        "to_email": "invalid-email",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_send_test_email_missing_fields(client, auth_headers):
    """Test test email task with missing required fields."""
    task_data = {
        "to_email": "test@example.com",
        # Missing subject and body
    }
    
    response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    
    assert response.status_code == 422

def test_send_test_email_unauthorized(client):
    """Test test email task without authentication."""
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    response = client.post("/tasks/send-test-email", json=task_data)
    
    assert response.status_code == 403

def test_get_task_status_success(client, auth_headers):
    """Test successful task status retrieval."""
    # First create a task
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    create_response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    assert create_response.status_code == 200
    
    task_id = create_response.json()["task_id"]
    
    # Now get the status
    response = client.get(f"/tasks/status/{task_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["task_id"] == task_id
    assert data["status"] in ["PENDING", "SUCCESS", "FAILURE", "RETRY", "REVOKED"]

def test_get_task_status_invalid_task_id(client, auth_headers):
    """Test task status retrieval with invalid task ID."""
    response = client.get("/tasks/status/invalid-task-id", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "PENDING"  # Invalid task IDs return PENDING

def test_get_task_status_nonexistent_task_id(client, auth_headers):
    """Test task status retrieval with non-existent task ID."""
    response = client.get("/tasks/status/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "status" in data
    assert data["status"] == "PENDING"

def test_get_task_status_unauthorized(client):
    """Test task status retrieval without authentication."""
    response = client.get("/tasks/status/some-task-id")
    
    assert response.status_code == 403

def test_task_status_response_structure(client, auth_headers):
    """Test that task status response has expected structure."""
    # Create a task
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    create_response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    assert create_response.status_code == 200
    
    task_id = create_response.json()["task_id"]
    
    # Get status
    response = client.get(f"/tasks/status/{task_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "task_id" in data
    assert "status" in data
    
    # Check optional fields based on status
    if data["status"] == "PENDING":
        assert "info" in data
    elif data["status"] == "FAILURE":
        assert "info" in data
    else:
        # SUCCESS or other statuses
        assert "result" in data

def test_multiple_task_creation(client, auth_headers):
    """Test creating multiple tasks."""
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    # Create multiple tasks
    task_ids = []
    for i in range(3):
        response = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
        assert response.status_code == 200
        task_ids.append(response.json()["task_id"])
    
    # All task IDs should be unique
    assert len(set(task_ids)) == 3
    
    # All should have PENDING status initially
    for task_id in task_ids:
        status_response = client.get(f"/tasks/status/{task_id}", headers=auth_headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "PENDING"

def test_task_endpoints_with_different_admin(client, auth_headers, admin_user2, admin_token2):
    """Test task endpoints with different admin user."""
    # Create task with first admin
    task_data = {
        "to_email": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email body"
    }
    
    response1 = client.post("/tasks/send-test-email", json=task_data, headers=auth_headers)
    assert response1.status_code == 200
    task_id1 = response1.json()["task_id"]
    
    # Create task with second admin
    response2 = client.post("/tasks/send-test-email", json=task_data, headers=admin_token2)
    assert response2.status_code == 200
    task_id2 = response2.json()["task_id"]
    
    # Both admins should be able to check status of any task
    status1 = client.get(f"/tasks/status/{task_id1}", headers=admin_token2)
    assert status1.status_code == 200
    
    status2 = client.get(f"/tasks/status/{task_id2}", headers=auth_headers)
    assert status2.status_code == 200
