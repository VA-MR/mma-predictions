"""API routes module."""

from .events import router as events_router
from .fights import router as fights_router
from .fighters import router as fighters_router
from .predictions import router as predictions_router
from .scorecards import router as scorecards_router
from .users import router as users_router
from .auth import router as auth_router
from .admin import router as admin_router

__all__ = [
    "events_router",
    "fights_router",
    "fighters_router",
    "predictions_router",
    "scorecards_router",
    "users_router",
    "auth_router",
    "admin_router",
]

