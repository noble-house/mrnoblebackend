import pytest
from fastapi.testclient import TestClient

def test_cache_status_success(client, auth_headers):
    """Test successful cache status retrieval."""
    response = client.get("/cache/status", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "info" in data
    assert data["status"] in ["ok", "error"]

def test_cache_status_unauthorized(client):
    """Test cache status without authentication."""
    response = client.get("/cache/status")
    
    assert response.status_code == 403

def test_cache_clear_success(client, auth_headers):
    """Test successful cache clearing."""
    response = client.post("/cache/clear", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "cleared successfully" in data["message"]

def test_cache_clear_unauthorized(client):
    """Test cache clear without authentication."""
    response = client.post("/cache/clear")
    
    assert response.status_code == 403

def test_cache_clear_multiple_times(client, auth_headers):
    """Test clearing cache multiple times."""
    # First clear
    response1 = client.post("/cache/clear", headers=auth_headers)
    assert response1.status_code == 200
    
    # Second clear
    response2 = client.post("/cache/clear", headers=auth_headers)
    assert response2.status_code == 200
    
    # Both should succeed
    data1 = response1.json()
    data2 = response2.json()
    assert "message" in data1
    assert "message" in data2

def test_cache_status_after_clear(client, auth_headers):
    """Test cache status after clearing."""
    # Clear cache first
    clear_response = client.post("/cache/clear", headers=auth_headers)
    assert clear_response.status_code == 200
    
    # Check status
    status_response = client.get("/cache/status", headers=auth_headers)
    assert status_response.status_code == 200
    data = status_response.json()
    assert "status" in data
    assert "info" in data

def test_cache_endpoints_with_different_admin(client, auth_headers, admin_user2, admin_token2):
    """Test cache endpoints with different admin user."""
    # Test status with different admin
    status_response = client.get("/cache/status", headers=admin_token2)
    assert status_response.status_code == 200
    
    # Test clear with different admin
    clear_response = client.post("/cache/clear", headers=admin_token2)
    assert clear_response.status_code == 200

def test_cache_status_info_structure(client, auth_headers):
    """Test that cache status info has expected structure."""
    response = client.get("/cache/status", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "info" in data
    
    # Info should be a dictionary (Redis info command result)
    assert isinstance(data["info"], dict)

def test_cache_clear_response_structure(client, auth_headers):
    """Test that cache clear response has expected structure."""
    response = client.post("/cache/clear", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0

def test_cache_endpoints_invalid_methods(client, auth_headers):
    """Test cache endpoints with invalid HTTP methods."""
    # Status endpoint should only accept GET
    response = client.post("/cache/status", headers=auth_headers)
    assert response.status_code == 405  # Method Not Allowed
    
    # Clear endpoint should only accept POST
    response = client.get("/cache/clear", headers=auth_headers)
    assert response.status_code == 405  # Method Not Allowed
