"""Admin authentication with session-based auth."""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import HTTPException, status, Request, Response
from pydantic import BaseModel


# Configuration from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin123")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123")

# Warn if using default credentials
if ADMIN_USERNAME == "Admin123" or ADMIN_PASSWORD == "Admin123":
    print("⚠️  WARNING: Using default admin credentials. Set ADMIN_USERNAME and ADMIN_PASSWORD env vars in production!")

# Session configuration
SESSION_EXPIRY_HOURS = 24
SESSION_COOKIE_NAME = "admin_session"

# Production detection - secure cookies when not in local development
IS_PRODUCTION = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PRODUCTION", "false").lower() == "true"

# In-memory session store: {token: expiry_datetime}
_active_sessions: Dict[str, datetime] = {}


class AdminLoginRequest(BaseModel):
    """Request body for admin login."""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Response for successful admin login."""
    success: bool
    message: str


def _hash_password(password: str) -> str:
    """Hash password for comparison (simple hash for env var comparison)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_admin_credentials(username: str, password: str) -> bool:
    """
    Verify admin credentials against environment variables.
    
    Args:
        username: Provided username
        password: Provided password
        
    Returns:
        True if credentials are valid
    """
    return (
        secrets.compare_digest(username, ADMIN_USERNAME) and
        secrets.compare_digest(password, ADMIN_PASSWORD)
    )


def create_admin_session() -> str:
    """
    Create a new admin session.
    
    Returns:
        Session token string
    """
    # Clean up expired sessions first
    _cleanup_expired_sessions()
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store with expiry time
    expiry = datetime.now(timezone.utc) + timedelta(hours=SESSION_EXPIRY_HOURS)
    _active_sessions[token] = expiry
    
    return token


def verify_admin_session(token: Optional[str]) -> bool:
    """
    Verify if a session token is valid.
    
    Args:
        token: Session token to verify
        
    Returns:
        True if session is valid and not expired
    """
    if not token:
        return False
    
    expiry = _active_sessions.get(token)
    if not expiry:
        return False
    
    # Check if expired
    if datetime.now(timezone.utc) > expiry:
        # Remove expired session
        del _active_sessions[token]
        return False
    
    return True


def invalidate_admin_session(token: Optional[str]) -> None:
    """
    Invalidate an admin session.
    
    Args:
        token: Session token to invalidate
    """
    if token and token in _active_sessions:
        del _active_sessions[token]


def _cleanup_expired_sessions() -> None:
    """Remove all expired sessions from memory."""
    now = datetime.now(timezone.utc)
    expired = [token for token, expiry in _active_sessions.items() if now > expiry]
    for token in expired:
        del _active_sessions[token]


def get_session_token_from_request(request: Request) -> Optional[str]:
    """
    Extract session token from request cookies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Session token or None
    """
    return request.cookies.get(SESSION_COOKIE_NAME)


def set_session_cookie(response: Response, token: str) -> None:
    """
    Set session cookie on response.
    
    Args:
        response: FastAPI response object
        token: Session token to set
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,  # Secure cookies in production (HTTPS)
        samesite="lax",  # Lax is appropriate for same-site requests
        max_age=SESSION_EXPIRY_HOURS * 3600,
    )


def clear_session_cookie(response: Response) -> None:
    """
    Clear session cookie from response.
    
    Args:
        response: FastAPI response object
    """
    response.delete_cookie(key=SESSION_COOKIE_NAME)


async def require_admin(request: Request) -> None:
    """
    Dependency to require admin authentication.
    
    Raises:
        HTTPException: If not authenticated
    """
    token = get_session_token_from_request(request)
    
    if not verify_admin_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )

