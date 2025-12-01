"""Pydantic schemas for API request/response models."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


# Enums
class PredictedWinnerEnum(str, Enum):
    FIGHTER1 = "fighter1"
    FIGHTER2 = "fighter2"


class WinMethodEnum(str, Enum):
    KO_TKO = "ko_tko"
    SUBMISSION = "submission"
    DECISION = "decision"
    DQ = "dq"


# Fighter schemas
class FighterBase(BaseModel):
    name: str
    country: Optional[str] = None
    wins: int = 0
    losses: int = 0
    draws: int = 0
    profile_url: Optional[str] = None


class FighterResponse(FighterBase):
    id: int
    record: str

    class Config:
        from_attributes = True


# Fight schemas
class FightBase(BaseModel):
    card_type: str = "main"
    weight_class: Optional[str] = None
    rounds: Optional[int] = None
    scheduled_time: Optional[str] = None
    fight_order: Optional[int] = None


class FightResponse(FightBase):
    id: int
    event_id: int
    fighter1: Optional[FighterResponse] = None
    fighter2: Optional[FighterResponse] = None

    class Config:
        from_attributes = True


class FightWithStatsResponse(FightResponse):
    prediction_stats: Optional[Dict[str, Any]] = None
    scorecard_stats: Optional[Dict[str, Any]] = None


# Main event info for event cards
class MainEventInfo(BaseModel):
    fighter1_name: Optional[str] = None
    fighter2_name: Optional[str] = None
    weight_class: Optional[str] = None


# Event schemas
class EventBase(BaseModel):
    name: str
    organization: str
    event_date: Optional[date] = None
    time_msk: Optional[str] = None
    location: Optional[str] = None
    is_upcoming: bool = True


class EventResponse(EventBase):
    id: int
    slug: str
    url: str
    fight_count: int = 0
    main_event: Optional[MainEventInfo] = None

    class Config:
        from_attributes = True


class EventDetailResponse(EventResponse):
    fights: List[FightResponse] = []


# User schemas
class TelegramAuthData(BaseModel):
    """Data received from Telegram Login Widget."""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    photo_url: Optional[str] = None
    display_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_predictions: int
    total_scorecards: int
    predictions_by_method: Dict[str, int]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Prediction schemas
class PredictionCreate(BaseModel):
    fight_id: int
    predicted_winner: PredictedWinnerEnum
    win_method: WinMethodEnum
    confidence: Optional[int] = Field(None, ge=1, le=5)


class PredictionResponse(BaseModel):
    id: int
    user_id: int
    fight_id: int
    predicted_winner: PredictedWinnerEnum
    win_method: WinMethodEnum
    confidence: Optional[int] = None
    created_at: datetime
    user: Optional[UserResponse] = None
    fight: Optional["FightResponse"] = None

    class Config:
        from_attributes = True


class PredictionStatsResponse(BaseModel):
    total_predictions: int
    fighter1_picks: int
    fighter2_picks: int
    fighter1_percentage: float
    fighter2_percentage: float
    methods: Dict[str, Dict[str, int]]


# Scorecard schemas
class RoundScoreCreate(BaseModel):
    round_number: int = Field(..., ge=1, le=5)
    fighter1_score: int = Field(..., ge=7, le=10)
    fighter2_score: int = Field(..., ge=7, le=10)


class RoundScoreResponse(BaseModel):
    id: int
    round_number: int
    fighter1_score: int
    fighter2_score: int

    class Config:
        from_attributes = True


class ScorecardCreate(BaseModel):
    fight_id: int
    round_scores: List[RoundScoreCreate]


class ScorecardResponse(BaseModel):
    id: int
    user_id: int
    fight_id: int
    created_at: datetime
    round_scores: List[RoundScoreResponse] = []
    total_fighter1: int
    total_fighter2: int
    winner: Optional[str] = None
    user: Optional[UserResponse] = None
    fight: Optional["FightResponse"] = None

    class Config:
        from_attributes = True


class ScorecardStatsResponse(BaseModel):
    total_scorecards: int
    rounds: Dict[int, Dict[str, float]]
    average_total_fighter1: float
    average_total_fighter2: float
    fighter1_wins: int
    fighter2_wins: int
    draws: int
    fighter1_win_percentage: float
    fighter2_win_percentage: float


# Combined stats response
class FightStatsResponse(BaseModel):
    fight: FightResponse
    prediction_stats: PredictionStatsResponse
    scorecard_stats: ScorecardStatsResponse


# API response wrappers
class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

