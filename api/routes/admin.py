"""Admin routes for CRUD operations on entities."""

from typing import List, Optional
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import Database
from database.models import (
    Fighter,
    Event,
    Fight,
    FightResult,
    OfficialScorecard,
    OfficialRoundScore,
)
from api.auth import get_db
from api.converters import event_to_response, fight_to_response
from api.schemas import (
    FighterCreateUpdate,
    FighterResponse,
    EventCreateUpdate,
    EventResponse,
    FightCreateUpdate,
    FightResponse,
    OrganizationResponse,
    FightResultCreate,
    FightResultResponse,
)
from api.services.result_resolution import resolve_fight_result
from api.admin_auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    verify_admin_credentials,
    create_admin_session,
    verify_admin_session,
    invalidate_admin_session,
    get_session_token_from_request,
    set_session_cookie,
    clear_session_cookie,
    require_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ========== AUTHENTICATION ENDPOINTS ==========

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    response: Response,
):
    """
    Admin login endpoint.
    Verifies credentials and creates a session cookie.
    """
    if not verify_admin_credentials(login_data.username, login_data.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Create session and set cookie
    token = create_admin_session()
    set_session_cookie(response, token)
    
    return AdminLoginResponse(
        success=True,
        message="Login successful"
    )


@router.post("/logout", response_model=AdminLoginResponse)
async def admin_logout(
    request: Request,
    response: Response,
):
    """
    Admin logout endpoint.
    Invalidates the current session and clears the cookie.
    """
    token = get_session_token_from_request(request)
    invalidate_admin_session(token)
    clear_session_cookie(response)
    
    return AdminLoginResponse(
        success=True,
        message="Logged out successfully"
    )


@router.get("/me")
async def admin_me(request: Request):
    """
    Check if current session is valid.
    Returns 200 if authenticated, 401 if not.
    """
    token = get_session_token_from_request(request)
    
    if not verify_admin_session(token):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return {"authenticated": True}


# ========== HELPER FUNCTIONS ==========

def update_event_status(session, event_id: int):
    """
    Check if all fights in an event have results.
    If yes, mark the event as not upcoming.
    """
    # Get the event
    event = session.get(Event, event_id)
    if not event:
        return
    
    # Get all fights for this event
    fights = session.query(Fight).filter(Fight.event_id == event_id).all()
    
    if not fights:
        return
    
    # Check if all fights have results
    all_have_results = all(fight.result is not None for fight in fights)
    
    # If all fights have results, mark event as not upcoming
    if all_have_results and event.is_upcoming:
        event.is_upcoming = False
        session.commit()


# ========== ORGANIZATIONS ==========

@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get list of all organizations (unique from events)."""
    with db.get_session() as session:
        # Get unique organizations from events
        stmt = (
            select(Event.organization, func.count(Event.id).label('event_count'))
            .group_by(Event.organization)
            .order_by(Event.organization)
            .offset(skip)
            .limit(limit)
        )
        results = session.execute(stmt).all()
        
        return [
            OrganizationResponse(
                name=org,
                event_count=count
            )
            for org, count in results
        ]


# ========== FIGHTERS ==========

@router.get("/fighters", response_model=List[FighterResponse])
async def list_fighters(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get list of all fighters."""
    with db.get_session() as session:
        stmt = select(Fighter).order_by(Fighter.name)
        
        # Apply search filter BEFORE pagination
        if search:
            stmt = stmt.where(
                Fighter.name.ilike(f"%{search}%") |
                Fighter.name_english.ilike(f"%{search}%")
            )
        
        # Apply pagination after filtering
        stmt = stmt.offset(skip).limit(limit)
        
        fighters = session.execute(stmt).scalars().all()
        return list(fighters)


@router.get("/fighters/{fighter_id}", response_model=FighterResponse)
async def get_fighter(
    fighter_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get a specific fighter."""
    with db.get_session() as session:
        fighter = session.get(Fighter, fighter_id)
        if not fighter:
            raise HTTPException(status_code=404, detail="Fighter not found")
        return fighter


@router.post("/fighters", response_model=FighterResponse)
async def create_fighter(
    fighter: FighterCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Create a new fighter."""
    with db.get_session() as session:
        db_fighter = Fighter(**fighter.model_dump())
        session.add(db_fighter)
        session.commit()
        session.refresh(db_fighter)
        return db_fighter


@router.put("/fighters/{fighter_id}", response_model=FighterResponse)
async def update_fighter(
    fighter_id: int,
    fighter: FighterCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Update an existing fighter."""
    with db.get_session() as session:
        db_fighter = session.get(Fighter, fighter_id)
        if not db_fighter:
            raise HTTPException(status_code=404, detail="Fighter not found")
        
        for key, value in fighter.model_dump(exclude_unset=True).items():
            setattr(db_fighter, key, value)
        
        session.commit()
        session.refresh(db_fighter)
        return db_fighter


@router.delete("/fighters/{fighter_id}")
async def delete_fighter(
    fighter_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Delete a fighter."""
    with db.get_session() as session:
        db_fighter = session.get(Fighter, fighter_id)
        if not db_fighter:
            raise HTTPException(status_code=404, detail="Fighter not found")
        
        session.delete(db_fighter)
        session.commit()
        return {"success": True}


# ========== EVENTS ==========

@router.get("/events", response_model=List[EventResponse])
async def list_events(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    organization: Optional[str] = None,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get list of all events."""
    with db.get_session() as session:
        stmt = select(Event).order_by(Event.event_date.desc())
        
        # Apply filter before pagination
        if organization:
            stmt = stmt.where(Event.organization == organization)
        
        stmt = stmt.offset(skip).limit(limit)
        
        events = session.execute(stmt).scalars().all()
        return [event_to_response(event) for event in events]


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get a specific event."""
    with db.get_session() as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event_to_response(event)


@router.post("/events", response_model=EventResponse)
async def create_event(
    event: EventCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Create a new event."""
    with db.get_session() as session:
        db_event = Event(**event.model_dump())
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return event_to_response(db_event)


@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event: EventCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Update an existing event."""
    with db.get_session() as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        for key, value in event.model_dump(exclude_unset=True).items():
            setattr(db_event, key, value)
        
        session.commit()
        session.refresh(db_event)
        return event_to_response(db_event)


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Delete an event."""
    with db.get_session() as session:
        db_event = session.get(Event, event_id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        session.delete(db_event)
        session.commit()
        return {"success": True}


# ========== FIGHTS ==========

@router.get("/fights", response_model=List[FightResponse])
async def list_fights(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    event_id: Optional[int] = None,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get list of all fights."""
    with db.get_session() as session:
        stmt = select(Fight).order_by(Fight.id.desc())
        
        # Apply filter before pagination
        if event_id:
            stmt = stmt.where(Fight.event_id == event_id)
        
        stmt = stmt.offset(skip).limit(limit)
        
        fights = session.execute(stmt).scalars().all()
        return [fight_to_response(fight) for fight in fights]


@router.get("/fights/{fight_id}", response_model=FightResponse)
async def get_fight(
    fight_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get a specific fight."""
    with db.get_session() as session:
        fight = session.get(Fight, fight_id)
        if not fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        return fight_to_response(fight)


@router.post("/fights", response_model=FightResponse)
async def create_fight(
    fight: FightCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Create a new fight."""
    with db.get_session() as session:
        db_fight = Fight(**fight.model_dump())
        session.add(db_fight)
        session.commit()
        session.refresh(db_fight)
        return fight_to_response(db_fight)


@router.put("/fights/{fight_id}", response_model=FightResponse)
async def update_fight(
    fight_id: int,
    fight: FightCreateUpdate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Update an existing fight."""
    with db.get_session() as session:
        db_fight = session.get(Fight, fight_id)
        if not db_fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        
        for key, value in fight.model_dump(exclude_unset=True).items():
            setattr(db_fight, key, value)
        
        session.commit()
        session.refresh(db_fight)
        return fight_to_response(db_fight)


@router.delete("/fights/{fight_id}")
async def delete_fight(
    fight_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Delete a fight."""
    with db.get_session() as session:
        db_fight = session.get(Fight, fight_id)
        if not db_fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        
        session.delete(db_fight)
        session.commit()
        return {"success": True}


# ========== FIGHT RESULTS ==========

@router.get("/fights/{fight_id}/result", response_model=FightResultResponse)
async def get_fight_result(
    fight_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """Get the official result for a fight."""
    with db.get_session() as session:
        # Use eager loading to load the result with all relationships
        result = session.query(FightResult).options(
            selectinload(FightResult.official_scorecards).selectinload(OfficialScorecard.round_scores)
        ).filter(FightResult.fight_id == fight_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Fight result not found")
        
        # Make the object accessible outside the session
        session.expunge(result)
        return result


@router.post("/fights/{fight_id}/result", response_model=FightResultResponse)
async def create_fight_result(
    fight_id: int,
    result_data: FightResultCreate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Create official result for a fight and resolve all predictions/scorecards.
    """
    with db.get_session() as session:
        # Check if fight exists
        fight = session.get(Fight, fight_id)
        if not fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        
        # Check if result already exists
        if fight.result:
            raise HTTPException(
                status_code=400,
                detail="Fight result already exists. Use PUT to update."
            )
        
        # Create fight result
        db_result = FightResult(
            fight_id=fight_id,
            winner=result_data.winner,
            method=result_data.method,
            finish_round=result_data.finish_round,
            finish_time=result_data.finish_time,
            is_resolved=False
        )
        session.add(db_result)
        session.flush()  # Get the ID
        
        # Create official scorecards if provided
        for scorecard_data in result_data.official_scorecards:
            db_scorecard = OfficialScorecard(
                fight_result_id=db_result.id,
                judge_name=scorecard_data.judge_name
            )
            session.add(db_scorecard)
            session.flush()
            
            # Create round scores
            for round_score_data in scorecard_data.round_scores:
                db_round_score = OfficialRoundScore(
                    official_scorecard_id=db_scorecard.id,
                    round_number=round_score_data.round_number,
                    fighter1_score=round_score_data.fighter1_score,
                    fighter2_score=round_score_data.fighter2_score
                )
                session.add(db_round_score)
        
        session.commit()
        
        # Resolve predictions and scorecards
        resolution_stats = resolve_fight_result(session, db_result)
        
        # Check if all fights in the event have results, and update event status
        if fight.event_id:
            update_event_status(session, fight.event_id)
        
        # Reload with all relationships eagerly loaded
        result = session.query(FightResult).options(
            selectinload(FightResult.official_scorecards).selectinload(OfficialScorecard.round_scores)
        ).filter(FightResult.id == db_result.id).first()
        
        # Make the object accessible outside the session
        session.expunge(result)
        return result


@router.put("/fights/{fight_id}/result", response_model=FightResultResponse)
async def update_fight_result(
    fight_id: int,
    result_data: FightResultCreate,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Update official result for a fight and re-resolve all predictions/scorecards.
    """
    with db.get_session() as session:
        # Check if fight exists
        fight = session.get(Fight, fight_id)
        if not fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        
        # Check if result exists
        if not fight.result:
            raise HTTPException(
                status_code=404,
                detail="Fight result not found. Use POST to create."
            )
        
        db_result = fight.result
        
        # Update basic fields
        db_result.winner = result_data.winner
        db_result.method = result_data.method
        db_result.finish_round = result_data.finish_round
        db_result.finish_time = result_data.finish_time
        db_result.is_resolved = False
        
        # Delete existing official scorecards
        for scorecard in db_result.official_scorecards:
            session.delete(scorecard)
        session.flush()
        
        # Create new official scorecards
        for scorecard_data in result_data.official_scorecards:
            db_scorecard = OfficialScorecard(
                fight_result_id=db_result.id,
                judge_name=scorecard_data.judge_name
            )
            session.add(db_scorecard)
            session.flush()
            
            # Create round scores
            for round_score_data in scorecard_data.round_scores:
                db_round_score = OfficialRoundScore(
                    official_scorecard_id=db_scorecard.id,
                    round_number=round_score_data.round_number,
                    fighter1_score=round_score_data.fighter1_score,
                    fighter2_score=round_score_data.fighter2_score
                )
                session.add(db_round_score)
        
        session.commit()
        
        # Re-resolve predictions and scorecards
        resolution_stats = resolve_fight_result(session, db_result)
        
        # Check if all fights in the event have results, and update event status
        if fight.event_id:
            update_event_status(session, fight.event_id)
        
        # Reload with all relationships eagerly loaded
        result = session.query(FightResult).options(
            selectinload(FightResult.official_scorecards).selectinload(OfficialScorecard.round_scores)
        ).filter(FightResult.id == db_result.id).first()
        
        # Make the object accessible outside the session
        session.expunge(result)
        return result


@router.delete("/fights/{fight_id}/result")
async def delete_fight_result(
    fight_id: int,
    request: Request,
    db: Database = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Delete official result for a fight and unresolve all predictions/scorecards.
    """
    with db.get_session() as session:
        # Check if fight exists
        fight = session.get(Fight, fight_id)
        if not fight:
            raise HTTPException(status_code=404, detail="Fight not found")
        
        # Check if result exists
        if not fight.result:
            raise HTTPException(status_code=404, detail="Fight result not found")
        
        # Unresolve all predictions
        for prediction in fight.predictions:
            prediction.is_correct = None
            prediction.resolved_at = None
        
        # Unresolve all scorecards
        for scorecard in fight.scorecards:
            scorecard.correct_rounds = 0
            scorecard.total_rounds = 0
            scorecard.resolved_at = None
            for round_score in scorecard.round_scores:
                round_score.is_correct = None
        
        # Delete the result (cascades to official scorecards)
        session.delete(fight.result)
        session.commit()
        
        return {"success": True}
