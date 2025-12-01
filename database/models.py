"""SQLAlchemy models for MMA events, fights, fighters, and scoring."""

from datetime import datetime, date, timezone
from typing import Optional, List
from enum import Enum


def utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DateTime,
    Date,
    Time,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class WinMethod(str, Enum):
    """Possible methods of victory."""
    KO_TKO = "ko_tko"
    SUBMISSION = "submission"
    DECISION = "decision"
    DQ = "dq"


class PredictedWinner(str, Enum):
    """Which fighter is predicted to win."""
    FIGHTER1 = "fighter1"
    FIGHTER2 = "fighter2"


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Fighter(Base):
    """Fighter model storing individual fighter information."""
    
    __tablename__ = "fighters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_english: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    
    # Physical stats
    age: Mapped[Optional[int]] = mapped_column(Integer)
    height_cm: Mapped[Optional[int]] = mapped_column(Integer)
    weight_kg: Mapped[Optional[float]] = mapped_column(Integer)
    reach_cm: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Fighting info
    style: Mapped[Optional[str]] = mapped_column(String(100))
    weight_class: Mapped[Optional[str]] = mapped_column(String(50))
    ranking: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Win methods
    wins_ko_tko: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    wins_submission: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    wins_decision: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    # Loss methods
    losses_ko_tko: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    losses_submission: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    losses_decision: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    # Profile
    profile_url: Mapped[Optional[str]] = mapped_column(String(500))
    profile_scraped: Mapped[bool] = mapped_column(default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    
    # Relationships
    fights_as_fighter1: Mapped[List["Fight"]] = relationship(
        "Fight", foreign_keys="Fight.fighter1_id", back_populates="fighter1"
    )
    fights_as_fighter2: Mapped[List["Fight"]] = relationship(
        "Fight", foreign_keys="Fight.fighter2_id", back_populates="fighter2"
    )
    
    # Create index on name for faster lookups
    __table_args__ = (
        Index("idx_fighter_name", "name"),
    )
    
    @property
    def record(self) -> str:
        """Return fighter's record as string (W-L-D)."""
        return f"{self.wins}-{self.losses}-{self.draws}"
    
    def __repr__(self) -> str:
        return f"<Fighter(id={self.id}, name='{self.name}', record='{self.record}')>"


class Event(Base):
    """Event model storing MMA event information."""
    
    __tablename__ = "events"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(100), nullable=False)
    event_date: Mapped[Optional[date]] = mapped_column(Date)
    time_msk: Mapped[Optional[str]] = mapped_column(String(10))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_upcoming: Mapped[bool] = mapped_column(default=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    
    # Relationships
    fights: Mapped[List["Fight"]] = relationship(
        "Fight", back_populates="event", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_event_date", "event_date"),
        Index("idx_event_org", "organization"),
    )
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, name='{self.name}', date='{self.event_date}')>"


class Fight(Base):
    """Fight model storing individual fight information."""
    
    __tablename__ = "fights"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    fighter1_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fighters.id"))
    fighter2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fighters.id"))
    card_type: Mapped[str] = mapped_column(String(50), default="main")  # main/prelim
    weight_class: Mapped[Optional[str]] = mapped_column(String(100))
    rounds: Mapped[Optional[int]] = mapped_column(Integer)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))
    fight_order: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="fights")
    fighter1: Mapped[Optional["Fighter"]] = relationship(
        "Fighter", foreign_keys=[fighter1_id], back_populates="fights_as_fighter1"
    )
    fighter2: Mapped[Optional["Fighter"]] = relationship(
        "Fighter", foreign_keys=[fighter2_id], back_populates="fights_as_fighter2"
    )
    
    __table_args__ = (
        Index("idx_fight_event", "event_id"),
        UniqueConstraint(
            "event_id", "fighter1_id", "fighter2_id",
            name="uq_fight_matchup"
        ),
    )
    
    # Relationships for scoring
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="fight", cascade="all, delete-orphan"
    )
    scorecards: Mapped[List["Scorecard"]] = relationship(
        "Scorecard", back_populates="fight", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        f1_name = self.fighter1.name if self.fighter1 else "TBA"
        f2_name = self.fighter2.name if self.fighter2 else "TBA"
        return f"<Fight(id={self.id}, {f1_name} vs {f2_name})>"


class User(Base):
    """User model for Telegram-authenticated users."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    auth_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
    
    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="user", cascade="all, delete-orphan"
    )
    scorecards: Mapped[List["Scorecard"]] = relationship(
        "Scorecard", back_populates="user", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_user_telegram_id", "telegram_id"),
    )
    
    @property
    def display_name(self) -> str:
        """Return user's display name."""
        if self.username:
            return f"@{self.username}"
        full_name = self.first_name
        if self.last_name:
            full_name += f" {self.last_name}"
        return full_name
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, name='{self.display_name}')>"


class Prediction(Base):
    """Pre-fight prediction model - immutable once created."""
    
    __tablename__ = "predictions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fight_id: Mapped[int] = mapped_column(ForeignKey("fights.id"), nullable=False)
    predicted_winner: Mapped[PredictedWinner] = mapped_column(
        SQLEnum(PredictedWinner), nullable=False
    )
    win_method: Mapped[WinMethod] = mapped_column(SQLEnum(WinMethod), nullable=False)
    confidence: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 confidence level
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="predictions")
    fight: Mapped["Fight"] = relationship("Fight", back_populates="predictions")
    
    __table_args__ = (
        # One prediction per user per fight
        UniqueConstraint("user_id", "fight_id", name="uq_user_fight_prediction"),
        Index("idx_prediction_fight", "fight_id"),
        Index("idx_prediction_user", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Prediction(id={self.id}, user={self.user_id}, fight={self.fight_id}, winner={self.predicted_winner.value})>"


class Scorecard(Base):
    """Round-by-round scorecard model - immutable once created."""
    
    __tablename__ = "scorecards"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fight_id: Mapped[int] = mapped_column(ForeignKey("fights.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scorecards")
    fight: Mapped["Fight"] = relationship("Fight", back_populates="scorecards")
    round_scores: Mapped[List["RoundScore"]] = relationship(
        "RoundScore", back_populates="scorecard", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        # One scorecard per user per fight
        UniqueConstraint("user_id", "fight_id", name="uq_user_fight_scorecard"),
        Index("idx_scorecard_fight", "fight_id"),
        Index("idx_scorecard_user", "user_id"),
    )
    
    @property
    def total_fighter1(self) -> int:
        """Calculate total score for fighter 1."""
        return sum(rs.fighter1_score for rs in self.round_scores)
    
    @property
    def total_fighter2(self) -> int:
        """Calculate total score for fighter 2."""
        return sum(rs.fighter2_score for rs in self.round_scores)
    
    @property
    def winner(self) -> Optional[str]:
        """Determine the winner based on scores."""
        if self.total_fighter1 > self.total_fighter2:
            return "fighter1"
        elif self.total_fighter2 > self.total_fighter1:
            return "fighter2"
        return "draw"
    
    def __repr__(self) -> str:
        return f"<Scorecard(id={self.id}, user={self.user_id}, fight={self.fight_id}, score={self.total_fighter1}-{self.total_fighter2})>"


class RoundScore(Base):
    """Individual round score within a scorecard."""
    
    __tablename__ = "round_scores"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    scorecard_id: Mapped[int] = mapped_column(ForeignKey("scorecards.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4, or 5
    fighter1_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 7-10
    fighter2_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 7-10
    
    # Relationships
    scorecard: Mapped["Scorecard"] = relationship("Scorecard", back_populates="round_scores")
    
    __table_args__ = (
        # One score per round per scorecard
        UniqueConstraint("scorecard_id", "round_number", name="uq_scorecard_round"),
        Index("idx_roundscore_scorecard", "scorecard_id"),
    )
    
    def __repr__(self) -> str:
        return f"<RoundScore(round={self.round_number}, score={self.fighter1_score}-{self.fighter2_score})>"

