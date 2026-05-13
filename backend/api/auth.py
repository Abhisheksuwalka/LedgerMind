import os

from fastapi import Header, HTTPException


def _is_production() -> bool:
    return os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "")).lower() == "production"


async def verify_api_key(x_api_key: str = Header(default="")):
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        # Fail closed in production. Keep local-dev convenience when not production.
        if _is_production():
            raise HTTPException(
                status_code=500,
                detail="API_KEY is required in production but is not configured.",
            )
        return
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


async def verify_internal_secret(x_internal_secret: str = Header(default="")):
    expected = os.getenv("INTERNAL_API_SECRET", "").strip()
    if not expected:
        if _is_production():
            raise HTTPException(
                status_code=500,
                detail="INTERNAL_API_SECRET is required in production but is not configured.",
            )
        return
    if x_internal_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid internal secret")
