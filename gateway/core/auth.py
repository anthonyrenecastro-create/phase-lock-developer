from fastapi import Header, HTTPException

from gateway.core.config import load_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = load_settings()
    if settings.api_key is None:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
