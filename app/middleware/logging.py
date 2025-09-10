import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..services.logger import log_api_call

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract user info from token if available
        user_email = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # We could decode the JWT here to get user email, but for now just note auth is present
            user_email = "authenticated_user"
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log the API call
        log_api_call(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            response_time=process_time,
            user_email=user_email,
            query_params=dict(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return response
