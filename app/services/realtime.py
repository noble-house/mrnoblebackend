import secrets
import hashlib
import time
from typing import Dict, Any
from ..config import settings
from ..services.logger import get_logger

logger = get_logger("realtime")

def generate_webrtc_credentials(interview_link_id: int, application_id: int) -> Dict[str, Any]:
    """Generate WebRTC credentials for interview session."""
    try:
        # Generate session-specific credentials
        session_id = f"interview_{interview_link_id}_{application_id}"
        timestamp = int(time.time())
        
        # Create a secure token for this session
        token_data = f"{session_id}_{timestamp}_{secrets.token_urlsafe(16)}"
        session_token = hashlib.sha256(token_data.encode()).hexdigest()
        
        # Generate room ID for the interview
        room_id = f"mrnoble_interview_{interview_link_id}"
        
        # Return WebRTC configuration
        return {
            "session_token": session_token,
            "room_id": room_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "server_url": settings.APP_BASE_URL,
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"}
            ],
            "config": {
                "iceCandidatePoolSize": 10,
                "enableAudio": True,
                "enableVideo": True,
                "enableScreenShare": False
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate WebRTC credentials: {e}")
        # Return fallback credentials
        return {
            "session_token": secrets.token_urlsafe(32),
            "room_id": f"fallback_{interview_link_id}",
            "session_id": f"fallback_{interview_link_id}",
            "timestamp": int(time.time()),
            "server_url": settings.APP_BASE_URL,
            "ice_servers": [{"urls": "stun:stun.l.google.com:19302"}],
            "config": {
                "iceCandidatePoolSize": 10,
                "enableAudio": True,
                "enableVideo": True,
                "enableScreenShare": False
            }
        }
