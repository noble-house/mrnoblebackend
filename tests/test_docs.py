import pytest
from fastapi.testclient import TestClient

def test_get_openapi_json_success(client, auth_headers):
    """Test successful OpenAPI JSON retrieval."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that it's a valid OpenAPI schema
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert "components" in data
    
    # Check specific info fields
    assert data["info"]["title"] == "MrNoble API"
    assert data["info"]["version"] == "1.0.0"
    assert "description" in data["info"]
    
    # Check that our main endpoints are present
    paths = data["paths"]
    assert "/auth/login" in paths
    assert "/intake/job" in paths
    assert "/intake/candidate" in paths
    assert "/match" in paths
    assert "/interview/invite" in paths
    assert "/interview/confirm" in paths
    assert "/interview/join/{token}" in paths
    assert "/email/process" in paths
    assert "/score/{interview_id}/finalize" in paths
    assert "/rt/ephemeral" in paths
    assert "/cache/status" in paths
    assert "/cache/clear" in paths
    assert "/tasks/send-test-email" in paths
    assert "/tasks/status/{task_id}" in paths

def test_get_openapi_json_unauthorized(client):
    """Test OpenAPI JSON retrieval without authentication."""
    response = client.get("/docs/openapi.json")
    
    assert response.status_code == 403

def test_get_openapi_json_structure(client, auth_headers):
    """Test that OpenAPI JSON has proper structure."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check OpenAPI version
    assert data["openapi"].startswith("3.")
    
    # Check info section
    info = data["info"]
    assert "title" in info
    assert "version" in info
    assert "description" in info
    assert "contact" in info
    assert "license_info" in info
    
    # Check contact info
    contact = info["contact"]
    assert "name" in contact
    assert "email" in contact
    assert "url" in contact
    
    # Check license info
    license_info = info["license_info"]
    assert "name" in license_info
    assert "url" in license_info
    
    # Check servers
    assert "servers" in data
    assert len(data["servers"]) >= 2  # Production and development servers
    
    # Check tags
    assert "tags" in data
    tags = data["tags"]
    tag_names = [tag["name"] for tag in tags]
    expected_tags = [
        "authentication", "intake", "match", "interview", 
        "email", "scoring", "realtime", "cache", "tasks"
    ]
    for expected_tag in expected_tags:
        assert expected_tag in tag_names

def test_get_openapi_json_components(client, auth_headers):
    """Test that OpenAPI JSON includes proper components."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check components section
    assert "components" in data
    components = data["components"]
    
    # Check schemas
    assert "schemas" in components
    schemas = components["schemas"]
    
    # Check that our main schemas are present
    expected_schemas = [
        "IntakeJob", "IntakeCandidate", "MatchRequest", "InviteRequest",
        "ConfirmRequest", "AdminLogin", "AdminResponse", "Token",
        "JobResponse", "CandidateResponse", "ApplicationResponse",
        "InterviewLinkResponse", "ErrorResponse"
    ]
    
    for schema_name in expected_schemas:
        assert schema_name in schemas
    
    # Check security schemes
    assert "securitySchemes" in components
    security_schemes = components["securitySchemes"]
    assert "HTTPBearer" in security_schemes

def test_get_openapi_json_paths_structure(client, auth_headers):
    """Test that OpenAPI JSON paths have proper structure."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    paths = data["paths"]
    
    # Check a few key endpoints
    auth_login = paths["/auth/login"]
    assert "post" in auth_login
    post_method = auth_login["post"]
    assert "tags" in post_method
    assert "authentication" in post_method["tags"]
    assert "requestBody" in post_method
    assert "responses" in post_method
    
    # Check that most endpoints require authentication
    protected_endpoints = [
        "/intake/job", "/intake/candidate", "/match", 
        "/interview/invite", "/interview/confirm",
        "/score/{interview_id}/finalize", "/rt/ephemeral",
        "/cache/status", "/cache/clear", "/tasks/send-test-email",
        "/tasks/status/{task_id}"
    ]
    
    for endpoint in protected_endpoints:
        if endpoint in paths:
            # Check that the endpoint has security requirements
            for method in paths[endpoint]:
                if method in ["get", "post", "put", "delete"]:
                    method_def = paths[endpoint][method]
                    if "security" in method_def:
                        assert len(method_def["security"]) > 0

def test_get_openapi_json_with_different_admin(client, auth_headers, admin_user2, admin_token2):
    """Test OpenAPI JSON retrieval with different admin user."""
    response = client.get("/docs/openapi.json", headers=admin_token2)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return the same OpenAPI schema
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert data["info"]["title"] == "MrNoble API"

def test_get_openapi_json_content_type(client, auth_headers):
    """Test that OpenAPI JSON is returned with correct content type."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

def test_get_openapi_json_size(client, auth_headers):
    """Test that OpenAPI JSON is reasonably sized."""
    response = client.get("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 200
    content = response.content
    
    # Should be substantial but not too large
    assert len(content) > 1000  # At least 1KB
    assert len(content) < 100000  # Less than 100KB

def test_get_openapi_json_invalid_method(client, auth_headers):
    """Test OpenAPI endpoint with invalid HTTP method."""
    response = client.post("/docs/openapi.json", headers=auth_headers)
    
    assert response.status_code == 405  # Method Not Allowed
