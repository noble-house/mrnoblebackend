import pytest
from fastapi.testclient import TestClient

def test_login_success(client, admin_user):
    """Test successful admin login."""
    response = client.post("/auth/login", json={
        "email": admin_user.email,
        "password": "testpassword"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_login_invalid_email_format(client):
    """Test login with invalid email format."""
    response = client.post("/auth/login", json={
        "email": "invalid-email",
        "password": "password"
    })
    
    assert response.status_code == 422

def test_get_current_admin(client, auth_headers):
    """Test getting current admin information."""
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "is_active" in data

def test_get_current_admin_unauthorized(client):
    """Test getting current admin without authentication."""
    response = client.get("/auth/me")
    
    assert response.status_code == 403

def test_logout(client, auth_headers):
    """Test admin logout."""
    response = client.post("/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]

def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without authentication."""
    response = client.post("/intake/job", json={
        "title": "Test Job",
        "jd_text": "Test description",
        "must_have": ["Python"],
        "nice_to_have": []
    })
    
    assert response.status_code == 403

def test_protected_endpoint_with_auth(client, auth_headers):
    """Test accessing protected endpoint with authentication."""
    response = client.post("/intake/job", json={
        "title": "Test Job",
        "jd_text": "Test description",
        "must_have": ["Python"],
        "nice_to_have": []
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Job"
