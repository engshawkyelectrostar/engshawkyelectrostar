import hmac
import logging

from fastapi import Header, HTTPException, Request

from .config import load_settings

log = logging.getLogger("erp_api")


def require_auth(request: Request, x_api_key: str = Header(default="")) -> None:
    s = load_settings()
    if len(s.api_key) < 16:
        log.error("ERP_API_KEY not configured")
        raise HTTPException(500, "internal error")
    client_ip = request.client.host if request.client else ""
    if s.allowed_ips and client_ip not in s.allowed_ips:
        raise HTTPException(403, "forbidden")
    if not hmac.compare_digest(x_api_key.encode(), s.api_key.encode()):
        raise HTTPException(401, "unauthorized")
