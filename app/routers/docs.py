from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from ..services.auth import get_current_admin
from .. import models

router = APIRouter(prefix="/docs", tags=["documentation"])

@router.get("/api-guide", response_class=HTMLResponse)
def get_api_guide(current_admin: models.Admin = Depends(get_current_admin)):
    """Get comprehensive API usage guide."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MrNoble API Guide</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 30px; }
            .section { margin: 30px 0; }
            .endpoint { background: #f9f9f9; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0; }
            .method { font-weight: bold; color: #007bff; }
            .code { background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; }
            .note { background: #fff3cd; padding: 10px; border-radius: 3px; border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>MrNoble API Guide</h1>
            <p>Comprehensive guide to using the MrNoble API for hiring automation.</p>
        </div>

        <div class="section">
            <h2>Getting Started</h2>
            <p>The MrNoble API provides endpoints for managing the complete hiring pipeline:</p>
            <ul>
                <li>Job posting creation and management</li>
                <li>Candidate registration and resume processing</li>
                <li>AI-powered candidate-job matching</li>
                <li>Interview scheduling and management</li>
                <li>Real-time interview capabilities</li>
                <li>Analytics and reporting</li>
            </ul>
        </div>

        <div class="section">
            <h2>Authentication</h2>
            <p>Most endpoints require authentication. Get a JWT token by logging in:</p>
            <div class="endpoint">
                <span class="method">POST</span> /auth/login
                <div class="code">
                    {
                        "email": "admin@mrnoble.app",
                        "password": "your_password"
                    }
                </div>
            </div>
            <p>Include the token in the Authorization header:</p>
            <div class="code">Authorization: Bearer &lt;your-token&gt;</div>
        </div>

        <div class="section">
            <h2>Core Workflow</h2>
            
            <h3>1. Create a Job Posting</h3>
            <div class="endpoint">
                <span class="method">POST</span> /intake/job
                <div class="code">
                    {
                        "title": "Senior Full Stack Engineer",
                        "jd_text": "We are looking for a senior full stack engineer...",
                        "must_have": ["Python", "React", "PostgreSQL"],
                        "nice_to_have": ["Docker", "AWS"]
                    }
                </div>
            </div>

            <h3>2. Register a Candidate</h3>
            <div class="endpoint">
                <span class="method">POST</span> /intake/candidate
                <div class="code">
                    {
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "phone": "+1-555-123-4567",
                        "resume_url": "https://example.com/resume.pdf"
                    }
                </div>
            </div>

            <h3>3. Match Candidate to Job</h3>
            <div class="endpoint">
                <span class="method">POST</span> /match
                <div class="code">
                    {
                        "job_id": 1,
                        "candidate_id": 1
                    }
                </div>
            </div>

            <h3>4. Send Interview Invitation</h3>
            <div class="endpoint">
                <span class="method">POST</span> /interview/invite
                <div class="code">
                    {
                        "application_id": 1
                    }
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Background Jobs</h2>
            <p>Long-running operations are handled as background tasks:</p>
            
            <h3>Send Email in Background</h3>
            <div class="endpoint">
                <span class="method">POST</span> /tasks/send-invite
                <div class="code">
                    {
                        "application_id": 1,
                        "candidate_email": "john.doe@example.com",
                        "job_title": "Senior Full Stack Engineer",
                        "interview_url": "https://mrnoble.app/i/abc123"
                    }
                </div>
            </div>

            <h3>Check Task Status</h3>
            <div class="endpoint">
                <span class="method">GET</span> /tasks/status/{task_id}
            </div>
        </div>

        <div class="section">
            <h2>Real-time Interviews</h2>
            <p>For real-time interview capabilities:</p>
            
            <h3>Get Ephemeral Client Secret</h3>
            <div class="endpoint">
                <span class="method">POST</span> /rt/ephemeral
                <div class="code">
                    {
                        "model": "gpt-realtime",
                        "voice": "alloy",
                        "instructions": "You are a professional interviewer..."
                    }
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Analytics and Monitoring</h2>
            
            <h3>Cache Management</h3>
            <div class="endpoint">
                <span class="method">GET</span> /cache/status
                <span class="method">POST</span> /cache/clear
                <span class="method">GET</span> /cache/stats
            </div>

            <h3>Task Management</h3>
            <div class="endpoint">
                <span class="method">GET</span> /tasks/active
                <span class="method">GET</span> /tasks/stats
            </div>
        </div>

        <div class="section">
            <h2>Error Handling</h2>
            <p>The API returns structured error responses:</p>
            <div class="code">
                {
                    "detail": "Error message",
                    "error_code": "ERROR_CODE",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            </div>
            
            <h3>Common HTTP Status Codes</h3>
            <ul>
                <li><strong>200</strong> - Success</li>
                <li><strong>201</strong> - Created</li>
                <li><strong>400</strong> - Bad Request</li>
                <li><strong>401</strong> - Unauthorized</li>
                <li><strong>403</strong> - Forbidden</li>
                <li><strong>404</strong> - Not Found</li>
                <li><strong>422</strong> - Validation Error</li>
                <li><strong>500</strong> - Internal Server Error</li>
            </ul>
        </div>

        <div class="section">
            <h2>Rate Limiting</h2>
            <div class="note">
                <strong>Note:</strong> API calls are rate-limited to prevent abuse. 
                Contact support if you need higher limits.
            </div>
        </div>

        <div class="section">
            <h2>Support</h2>
            <p>For additional help:</p>
            <ul>
                <li>Email: support@mrnoble.app</li>
                <li>Documentation: <a href="/docs">Interactive API Docs</a></li>
                <li>OpenAPI Spec: <a href="/openapi.json">/openapi.json</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
