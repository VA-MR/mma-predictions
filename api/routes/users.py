"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database, User
from api.auth import get_db, get_current_user, require_auth
from api.schemas import UserResponse, UserStatsResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(require_auth),
):
    """Get current authenticated user's information."""
    return UserResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        photo_url=user.photo_url,
        display_name=user.display_name,
        created_at=user.created_at,
    )


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_current_user_stats(
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Get current authenticated user's statistics."""
    with db.get_session() as session:
        stats = db.get_user_stats(session, user.id)
        return UserStatsResponse(**stats)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_info(
    user_id: int,
    db: Database = Depends(get_db),
):
    """Get a user's public information by ID."""
    with db.get_session() as session:
        user = db.get_user_by_id(session, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        return UserResponse(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            photo_url=user.photo_url,
            display_name=user.display_name,
            created_at=user.created_at,
        )


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int,
    db: Database = Depends(get_db),
):
    """Get a user's public statistics by ID."""
    with db.get_session() as session:
        user = db.get_user_by_id(session, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        
        stats = db.get_user_stats(session, user_id)
        return UserStatsResponse(**stats)

