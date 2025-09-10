from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests, os
from ..config import settings

router = APIRouter(prefix="/rt", tags=["realtime"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Set on Railway
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

class EphemeralConfig(BaseModel):
    model: str = "gpt-realtime"  # latest GA realtime model
    voice: str | None = "alloy"  # choose from docs (e.g., "alloy", "marin", "cedar")
    instructions: str | None = "You are Mr Noble, a professional, concise interviewer. Ask one question at a time."
    # For MCP, you could include tools in the session object later.

@router.post("/ephemeral")
def create_ephemeral(cfg: EphemeralConfig):
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY not configured")

    # New GA endpoint for client secrets (Aug 28, 2025 blog)
    url = f"{OPENAI_BASE_URL}/v1/realtime/client_secrets"
    payload = {
        "model": cfg.model,
        "voice": cfg.voice,
        "instructions": cfg.instructions,
        "session": {
            "type": "realtime"
            # You can add MCP config here later: tools: [{type:"mcp", ...}]
        }
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    data = r.json()
    # Return only the ephemeral token and expiry to the browser
    client_secret = data.get("client_secret", {})
    return {
        "client_secret": {
            "value": client_secret.get("value"),
            "expires_at": client_secret.get("expires_at")
        }
    }
