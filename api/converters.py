"""Centralized model-to-schema converters for API responses."""

from typing import Optional

from database.models import Fight, Fighter, Prediction, Scorecard, User, Event
from api.schemas import (
    FightResponse,
    FighterResponse,
    PredictionResponse,
    ScorecardResponse,
    RoundScoreResponse,
    UserResponse,
    EventResponse,
    MainEventInfo,
)


def fighter_to_response(fighter: Fighter) -> FighterResponse:
    """Convert Fighter model to FighterResponse schema."""
    return FighterResponse(
        id=fighter.id,
        name=fighter.name,
        country=fighter.country,
        wins=fighter.wins,
        losses=fighter.losses,
        draws=fighter.draws,
        profile_url=fighter.profile_url,
        record=fighter.record,
    )


def fight_to_response(fight: Fight) -> FightResponse:
    """Convert Fight model to FightResponse schema."""
    fighter1 = None
    fighter2 = None

    if fight.fighter1:
        fighter1 = fighter_to_response(fight.fighter1)

    if fight.fighter2:
        fighter2 = fighter_to_response(fight.fighter2)

    return FightResponse(
        id=fight.id,
        event_id=fight.event_id,
        card_type=fight.card_type,
        weight_class=fight.weight_class,
        rounds=fight.rounds,
        scheduled_time=fight.scheduled_time,
        fight_order=fight.fight_order,
        fighter1=fighter1,
        fighter2=fighter2,
    )


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema."""
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


def prediction_to_response(
    prediction: Prediction,
    include_user: bool = True,
) -> PredictionResponse:
    """Convert Prediction model to PredictionResponse schema."""
    user_response = None
    if include_user and prediction.user:
        user_response = user_to_response(prediction.user)

    return PredictionResponse(
        id=prediction.id,
        user_id=prediction.user_id,
        fight_id=prediction.fight_id,
        predicted_winner=prediction.predicted_winner.value,
        win_method=prediction.win_method.value,
        confidence=prediction.confidence,
        created_at=prediction.created_at,
        user=user_response,
    )


def scorecard_to_response(
    scorecard: Scorecard,
    include_user: bool = True,
) -> ScorecardResponse:
    """Convert Scorecard model to ScorecardResponse schema."""
    user_response = None
    if include_user and scorecard.user:
        user_response = user_to_response(scorecard.user)

    round_scores = [
        RoundScoreResponse(
            id=rs.id,
            round_number=rs.round_number,
            fighter1_score=rs.fighter1_score,
            fighter2_score=rs.fighter2_score,
        )
        for rs in sorted(scorecard.round_scores, key=lambda x: x.round_number)
    ]

    return ScorecardResponse(
        id=scorecard.id,
        user_id=scorecard.user_id,
        fight_id=scorecard.fight_id,
        created_at=scorecard.created_at,
        round_scores=round_scores,
        total_fighter1=scorecard.total_fighter1,
        total_fighter2=scorecard.total_fighter2,
        winner=scorecard.winner,
        user=user_response,
    )


def get_main_event_info(event: Event) -> Optional[MainEventInfo]:
    """Get main event fight info for an event."""
    if not event.fights:
        return None

    # Find the main event - highest fight_order or first main card fight
    main_fights = [f for f in event.fights if f.card_type == "main"]
    if main_fights:
        # Sort by fight_order descending (main event is usually last/highest)
        main_fights.sort(key=lambda f: f.fight_order or 0, reverse=True)
        main_fight = main_fights[0]
    else:
        # Fallback to first fight
        main_fight = event.fights[0]

    return MainEventInfo(
        fighter1_name=main_fight.fighter1.name if main_fight.fighter1 else None,
        fighter2_name=main_fight.fighter2.name if main_fight.fighter2 else None,
        weight_class=main_fight.weight_class,
    )


def event_to_response(event: Event) -> EventResponse:
    """Convert Event model to EventResponse schema."""
    return EventResponse(
        id=event.id,
        name=event.name,
        organization=event.organization,
        event_date=event.event_date,
        time_msk=event.time_msk,
        location=event.location,
        is_upcoming=event.is_upcoming,
        slug=event.slug,
        url=event.url,
        fight_count=len(event.fights),
        main_event=get_main_event_info(event),
    )

