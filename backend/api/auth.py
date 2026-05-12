import os
from fastapi import Header, HTTPException, Security

async def verify_api_key(x_api_key: str = Header(default="")):
    expected = os.getenv("API_KEY", "")
    if not expected:
        # Dev mode: API_KEY not set in .env — all requests are allowed.
        # Set API_KEY in production to enforce authentication.
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
