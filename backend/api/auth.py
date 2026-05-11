import os
from fastapi import Header, HTTPException, Security

async def verify_api_key(x_api_key: str = Header(default="")):
    expected = os.getenv("API_KEY", "")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
