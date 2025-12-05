"""Authentication routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database
from api.auth import verify_telegram_auth, create_access_token, get_db
from api.schemas import TelegramAuthData, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(
    auth_data: TelegramAuthData,
    db: Database = Depends(get_db),
):
    """Authenticate user via Telegram Login Widget.
    
    Verifies the authentication data from Telegram and creates/updates
    the user in the database. Returns a JWT token for future requests.
    """
    # Convert to dict for verification
    auth_dict = auth_data.model_dump()
    
    # Verify authentication
    if not verify_telegram_auth(auth_dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data",
        )
    
    # Check if auth is not too old (within 24 hours)
    auth_datetime = datetime.fromtimestamp(auth_data.auth_date, tz=timezone.utc)
    if (datetime.now(timezone.utc) - auth_datetime).days > 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication data expired. Please sign in again.",
        )
    
    # Create or update user
    with db.get_session() as session:
        user = db.get_or_create_user(
            session=session,
            telegram_id=auth_data.id,
            first_name=auth_data.first_name,
            last_name=auth_data.last_name,
            username=auth_data.username,
            photo_url=auth_data.photo_url,
            auth_date=auth_datetime,
        )
        session.commit()
        
        # Create access token
        token = create_access_token(user.id, user.telegram_id)
        
        # Prepare response
        user_response = UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=user.photo_url,
            display_name=user.display_name,
            created_at=user.created_at,
        )
        
        return TokenResponse(
            access_token=token,
            user=user_response,
        )


@router.post("/logout")
async def logout():
    """Logout endpoint (client should discard the token)."""
    return {"message": "Logged out successfully. Please discard your token."}

