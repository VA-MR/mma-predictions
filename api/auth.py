"""Telegram authentication utilities."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel

from database import Database, User

# Configuration
# Generate a random secret if not provided (for development only)
_default_secret = secrets.token_urlsafe(32)
SECRET_KEY = os.getenv("JWT_SECRET", _default_secret)
if SECRET_KEY == _default_secret:
    print("⚠️  WARNING: Using auto-generated JWT_SECRET. Set JWT_SECRET env var in production!")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    user_id: int
    telegram_id: int


def verify_telegram_auth(auth_data: dict) -> bool:
    """Verify Telegram Login Widget authentication data.
    
    Args:
        auth_data: Dictionary containing Telegram auth data including hash.
        
    Returns:
        True if authentication is valid.
    """
    if not TELEGRAM_BOT_TOKEN:
        # In development, skip verification if no token is set
        return True
    
    # Extract hash and create data check string
    received_hash = auth_data.pop("hash", "")
    
    # Sort keys and create data check string
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
    data_check_string = "\n".join(data_check_arr)
    
    # Create secret key from bot token
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    
    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Put hash back for later use
    auth_data["hash"] = received_hash
    
    return hmac.compare_digest(calculated_hash, received_hash)


def create_access_token(user_id: int, telegram_id: int) -> str:
    """Create JWT access token.
    
    Args:
        user_id: Database user ID.
        telegram_id: Telegram user ID.
        
    Returns:
        JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "telegram_id": telegram_id,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and verify JWT token.
    
    Args:
        token: JWT token string.
        
    Returns:
        TokenData if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        telegram_id = int(payload.get("telegram_id", 0))
        
        if not user_id or not telegram_id:
            return None
            
        return TokenData(user_id=user_id, telegram_id=telegram_id)
    except JWTError:
        return None


def get_db() -> Database:
    """Get database instance (singleton)."""
    from api.main import get_database
    return get_database()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Database = Depends(get_db),
) -> Optional[User]:
    """Get current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token credentials.
        db: Database instance.
        
    Returns:
        User if authenticated, None otherwise.
    """
    if not credentials:
        return None
    
    token_data = decode_token(credentials.credentials)
    if not token_data:
        return None
    
    with db.get_session() as session:
        user = db.get_user_by_id(session, token_data.user_id)
        if user and user.telegram_id == token_data.telegram_id:
            # Detach from session for use outside
            session.expunge(user)
            return user
    
    return None


async def require_auth(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authenticated user.
    
    Args:
        user: Current user from get_current_user.
        
    Returns:
        Authenticated user.
        
    Raises:
        HTTPException: If user is not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

