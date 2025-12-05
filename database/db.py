"""Database operations for MMA scraper and scoring app."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


def utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session, sessionmaker
from rich.console import Console

from .models import (
    Base, Event, Fight, Fighter,
    User, Prediction, Scorecard, RoundScore,
    PredictedWinner, WinMethod,
)

console = Console()


class Database:
    """Database manager for MMA scraper data."""
    
    def __init__(self, db_path: str = "mma_data.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        console.print("[green]✓[/green] Database tables created/verified")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    # Fighter operations
    def get_or_create_fighter(
        self,
        session: Session,
        name: str,
        country: Optional[str] = None,
        wins: int = 0,
        losses: int = 0,
        draws: int = 0,
        profile_url: Optional[str] = None,
        # Extended stats
        name_english: Optional[str] = None,
        age: Optional[int] = None,
        height_cm: Optional[int] = None,
        weight_kg: Optional[float] = None,
        reach_cm: Optional[int] = None,
        style: Optional[str] = None,
        ranking: Optional[str] = None,
        wins_ko_tko: Optional[int] = None,
        wins_submission: Optional[int] = None,
        wins_decision: Optional[int] = None,
        losses_ko_tko: Optional[int] = None,
        losses_submission: Optional[int] = None,
        losses_decision: Optional[int] = None,
        profile_scraped: bool = False,
    ) -> Fighter:
        """Get existing fighter or create new one.
        
        Args:
            session: Database session.
            name: Fighter name.
            country: Fighter's country.
            wins: Number of wins.
            losses: Number of losses.
            draws: Number of draws.
            profile_url: URL to fighter's profile.
            + extended stats
            
        Returns:
            Fighter instance.
        """
        # Try to find existing fighter by name
        stmt = select(Fighter).where(Fighter.name == name)
        fighter = session.execute(stmt).scalar_one_or_none()
        
        if fighter:
            # Update record if it changed
            if (fighter.wins != wins or fighter.losses != losses or 
                fighter.draws != draws):
                fighter.wins = wins
                fighter.losses = losses
                fighter.draws = draws
                fighter.updated_at = utc_now()
            if country and fighter.country != country:
                fighter.country = country
            if profile_url and fighter.profile_url != profile_url:
                fighter.profile_url = profile_url
            
            # Update extended stats if provided
            if name_english:
                fighter.name_english = name_english
            if age is not None:
                fighter.age = age
            if height_cm is not None:
                fighter.height_cm = height_cm
            if weight_kg is not None:
                fighter.weight_kg = weight_kg
            if reach_cm is not None:
                fighter.reach_cm = reach_cm
            if style:
                fighter.style = style
            if ranking:
                fighter.ranking = ranking
            if wins_ko_tko is not None:
                fighter.wins_ko_tko = wins_ko_tko
            if wins_submission is not None:
                fighter.wins_submission = wins_submission
            if wins_decision is not None:
                fighter.wins_decision = wins_decision
            if losses_ko_tko is not None:
                fighter.losses_ko_tko = losses_ko_tko
            if losses_submission is not None:
                fighter.losses_submission = losses_submission
            if losses_decision is not None:
                fighter.losses_decision = losses_decision
            if profile_scraped:
                fighter.profile_scraped = profile_scraped
                
            return fighter
        
        # Create new fighter
        fighter = Fighter(
            name=name,
            name_english=name_english,
            country=country,
            wins=wins,
            losses=losses,
            draws=draws,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            reach_cm=reach_cm,
            style=style,
            ranking=ranking,
            wins_ko_tko=wins_ko_tko,
            wins_submission=wins_submission,
            wins_decision=wins_decision,
            losses_ko_tko=losses_ko_tko,
            losses_submission=losses_submission,
            losses_decision=losses_decision,
            profile_url=profile_url,
            profile_scraped=profile_scraped,
        )
        session.add(fighter)
        session.flush()  # Get the ID
        return fighter
    
    def get_fighters_without_profiles(self, session: Session) -> List[Fighter]:
        """Get fighters that haven't had their profiles scraped yet."""
        stmt = select(Fighter).where(Fighter.profile_scraped == False)
        return list(session.execute(stmt).scalars().all())
    
    def get_fighter_by_name(self, session: Session, name: str) -> Optional[Fighter]:
        """Get fighter by name."""
        stmt = select(Fighter).where(Fighter.name == name)
        return session.execute(stmt).scalar_one_or_none()
    
    def get_fighter_by_id(self, session: Session, fighter_id: int) -> Optional[Fighter]:
        """Get fighter by ID."""
        stmt = select(Fighter).where(Fighter.id == fighter_id)
        return session.execute(stmt).scalar_one_or_none()
    
    def get_all_fighters(self, session: Session) -> List[Fighter]:
        """Get all fighters."""
        stmt = select(Fighter).order_by(Fighter.name)
        return list(session.execute(stmt).scalars().all())
    
    # Event operations
    def get_or_create_event(
        self,
        session: Session,
        name: str,
        organization: str,
        slug: str,
        url: str,
        event_date: Optional[datetime] = None,
        time_msk: Optional[str] = None,
        location: Optional[str] = None,
        is_upcoming: bool = True,
    ) -> Event:
        """Get existing event or create new one.
        
        Args:
            session: Database session.
            name: Event name.
            organization: MMA organization.
            slug: URL slug for the event.
            url: Full URL to event page.
            event_date: Date of the event.
            time_msk: Time in Moscow timezone.
            location: Event location.
            is_upcoming: Whether event is in the future.
            
        Returns:
            Event instance.
        """
        # Try to find existing event by slug
        stmt = select(Event).where(Event.slug == slug)
        event = session.execute(stmt).scalar_one_or_none()
        
        if event:
            # Update fields
            event.name = name
            event.organization = organization
            event.event_date = event_date
            event.time_msk = time_msk
            event.location = location
            event.is_upcoming = is_upcoming
            event.updated_at = utc_now()
            return event
        
        # Create new event
        event = Event(
            name=name,
            organization=organization,
            slug=slug,
            url=url,
            event_date=event_date,
            time_msk=time_msk,
            location=location,
            is_upcoming=is_upcoming,
        )
        session.add(event)
        session.flush()
        return event
    
    def get_event_by_slug(self, session: Session, slug: str) -> Optional[Event]:
        """Get event by slug."""
        stmt = select(Event).where(Event.slug == slug)
        return session.execute(stmt).scalar_one_or_none()
    
    def get_upcoming_events(self, session: Session) -> List[Event]:
        """Get all upcoming events."""
        stmt = (
            select(Event)
            .where(Event.is_upcoming == True)
            .order_by(Event.event_date)
        )
        return list(session.execute(stmt).scalars().all())
    
    def get_all_events(self, session: Session) -> List[Event]:
        """Get all events."""
        stmt = select(Event).order_by(Event.event_date.desc())
        return list(session.execute(stmt).scalars().all())
    
    # Fight operations
    def create_fight(
        self,
        session: Session,
        event: Event,
        fighter1: Optional[Fighter],
        fighter2: Optional[Fighter],
        card_type: str = "main",
        weight_class: Optional[str] = None,
        rounds: Optional[int] = None,
        scheduled_time: Optional[str] = None,
        fight_order: Optional[int] = None,
    ) -> Fight:
        """Create a new fight or update existing one.
        
        Args:
            session: Database session.
            event: Event the fight belongs to.
            fighter1: First fighter.
            fighter2: Second fighter.
            card_type: Type of card (main/prelim).
            weight_class: Weight class of the fight.
            rounds: Number of rounds.
            scheduled_time: Scheduled fight time.
            fight_order: Order of fight on the card.
            
        Returns:
            Fight instance.
        """
        # Check for existing fight
        stmt = select(Fight).where(
            Fight.event_id == event.id,
            Fight.fighter1_id == (fighter1.id if fighter1 else None),
            Fight.fighter2_id == (fighter2.id if fighter2 else None),
        )
        fight = session.execute(stmt).scalar_one_or_none()
        
        if fight:
            # Update existing fight
            fight.card_type = card_type
            fight.weight_class = weight_class
            fight.rounds = rounds
            fight.scheduled_time = scheduled_time
            fight.fight_order = fight_order
            fight.updated_at = utc_now()
            return fight
        
        # Create new fight
        fight = Fight(
            event_id=event.id,
            fighter1_id=fighter1.id if fighter1 else None,
            fighter2_id=fighter2.id if fighter2 else None,
            card_type=card_type,
            weight_class=weight_class,
            rounds=rounds,
            scheduled_time=scheduled_time,
            fight_order=fight_order,
        )
        session.add(fight)
        session.flush()
        return fight
    
    def get_fights_for_event(self, session: Session, event_id: int) -> List[Fight]:
        """Get all fights for an event."""
        stmt = (
            select(Fight)
            .where(Fight.event_id == event_id)
            .order_by(Fight.fight_order)
        )
        return list(session.execute(stmt).scalars().all())
    
    def clear_fights_for_event(self, session: Session, event_id: int) -> int:
        """Delete all fights for an event (used before re-scraping).
        
        Returns:
            Number of fights deleted.
        """
        fights = self.get_fights_for_event(session, event_id)
        count = len(fights)
        for fight in fights:
            session.delete(fight)
        return count
    
    # Statistics
    def get_stats(self, session: Session) -> dict:
        """Get database statistics."""
        events_count = session.query(Event).count()
        upcoming_count = session.query(Event).filter(Event.is_upcoming == True).count()
        fighters_count = session.query(Fighter).count()
        fights_count = session.query(Fight).count()
        users_count = session.query(User).count()
        predictions_count = session.query(Prediction).count()
        scorecards_count = session.query(Scorecard).count()
        
        return {
            "total_events": events_count,
            "upcoming_events": upcoming_count,
            "total_fighters": fighters_count,
            "total_fights": fights_count,
            "total_users": users_count,
            "total_predictions": predictions_count,
            "total_scorecards": scorecards_count,
        }
    
    # User operations
    def get_or_create_user(
        self,
        session: Session,
        telegram_id: int,
        first_name: str,
        auth_date: datetime,
        username: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> User:
        """Get existing user or create new one from Telegram auth.
        
        Args:
            session: Database session.
            telegram_id: Telegram user ID.
            first_name: User's first name.
            auth_date: Authentication timestamp.
            username: Telegram username.
            last_name: User's last name.
            photo_url: Profile photo URL.
            
        Returns:
            User instance.
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        user = session.execute(stmt).scalar_one_or_none()
        
        if user:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.photo_url = photo_url
            user.auth_date = auth_date
            user.updated_at = utc_now()
            return user
        
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            photo_url=photo_url,
            auth_date=auth_date,
        )
        session.add(user)
        session.flush()
        return user
    
    def get_user_by_telegram_id(self, session: Session, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        return session.execute(stmt).scalar_one_or_none()
    
    def get_user_by_id(self, session: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        return session.execute(stmt).scalar_one_or_none()
    
    # Prediction operations
    def create_prediction(
        self,
        session: Session,
        user_id: int,
        fight_id: int,
        predicted_winner: PredictedWinner,
        win_method: WinMethod,
        confidence: Optional[int] = None,
    ) -> Prediction:
        """Create a new prediction (immutable - will fail if one exists).
        
        Args:
            session: Database session.
            user_id: User making the prediction.
            fight_id: Fight being predicted.
            predicted_winner: Which fighter will win.
            win_method: How they will win.
            confidence: Confidence level (1-5).
            
        Returns:
            Prediction instance.
            
        Raises:
            ValueError: If prediction already exists.
        """
        # Check if prediction already exists
        existing = self.get_user_prediction_for_fight(session, user_id, fight_id)
        if existing:
            raise ValueError("Prediction already exists for this fight. Predictions cannot be changed.")
        
        prediction = Prediction(
            user_id=user_id,
            fight_id=fight_id,
            predicted_winner=predicted_winner,
            win_method=win_method,
            confidence=confidence,
        )
        session.add(prediction)
        session.flush()
        return prediction
    
    def get_user_prediction_for_fight(
        self, session: Session, user_id: int, fight_id: int
    ) -> Optional[Prediction]:
        """Get user's prediction for a specific fight."""
        stmt = select(Prediction).where(
            Prediction.user_id == user_id,
            Prediction.fight_id == fight_id,
        )
        return session.execute(stmt).scalar_one_or_none()
    
    def get_predictions_for_fight(self, session: Session, fight_id: int) -> List[Prediction]:
        """Get all predictions for a fight."""
        stmt = (
            select(Prediction)
            .where(Prediction.fight_id == fight_id)
            .order_by(Prediction.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())
    
    def get_user_predictions(self, session: Session, user_id: int) -> List[Prediction]:
        """Get all predictions by a user."""
        stmt = (
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())
    
    # Scorecard operations
    def create_scorecard(
        self,
        session: Session,
        user_id: int,
        fight_id: int,
        round_scores: List[Dict[str, int]],
    ) -> Scorecard:
        """Create a new scorecard with round scores (immutable).
        
        Args:
            session: Database session.
            user_id: User submitting the scorecard.
            fight_id: Fight being scored.
            round_scores: List of dicts with round_number, fighter1_score, fighter2_score.
            
        Returns:
            Scorecard instance.
            
        Raises:
            ValueError: If scorecard already exists.
        """
        # Check if scorecard already exists
        existing = self.get_user_scorecard_for_fight(session, user_id, fight_id)
        if existing:
            raise ValueError("Scorecard already exists for this fight. Scorecards cannot be changed.")
        
        scorecard = Scorecard(
            user_id=user_id,
            fight_id=fight_id,
        )
        session.add(scorecard)
        session.flush()
        
        # Add round scores
        for rs in round_scores:
            round_score = RoundScore(
                scorecard_id=scorecard.id,
                round_number=rs["round_number"],
                fighter1_score=rs["fighter1_score"],
                fighter2_score=rs["fighter2_score"],
            )
            session.add(round_score)
        
        session.flush()
        return scorecard
    
    def get_user_scorecard_for_fight(
        self, session: Session, user_id: int, fight_id: int
    ) -> Optional[Scorecard]:
        """Get user's scorecard for a specific fight."""
        stmt = select(Scorecard).where(
            Scorecard.user_id == user_id,
            Scorecard.fight_id == fight_id,
        )
        return session.execute(stmt).scalar_one_or_none()
    
    def get_scorecards_for_fight(self, session: Session, fight_id: int) -> List[Scorecard]:
        """Get all scorecards for a fight."""
        stmt = (
            select(Scorecard)
            .where(Scorecard.fight_id == fight_id)
            .order_by(Scorecard.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())
    
    def get_user_scorecards(self, session: Session, user_id: int) -> List[Scorecard]:
        """Get all scorecards by a user."""
        stmt = (
            select(Scorecard)
            .where(Scorecard.user_id == user_id)
            .order_by(Scorecard.created_at.desc())
        )
        return list(session.execute(stmt).scalars().all())
    
    # Aggregation / Crowd Wisdom
    def get_fight_prediction_stats(self, session: Session, fight_id: int) -> Dict[str, Any]:
        """Get aggregated prediction statistics for a fight.
        
        Returns:
            Dict with prediction counts and percentages.
        """
        predictions = self.get_predictions_for_fight(session, fight_id)
        total = len(predictions)
        
        if total == 0:
            return {
                "total_predictions": 0,
                "fighter1_picks": 0,
                "fighter2_picks": 0,
                "fighter1_percentage": 0,
                "fighter2_percentage": 0,
                "methods": {},
            }
        
        fighter1_picks = sum(1 for p in predictions if p.predicted_winner == PredictedWinner.FIGHTER1)
        fighter2_picks = total - fighter1_picks
        
        # Count by method
        methods: Dict[str, Dict[str, int]] = {}
        for method in WinMethod:
            method_preds = [p for p in predictions if p.win_method == method]
            methods[method.value] = {
                "fighter1": sum(1 for p in method_preds if p.predicted_winner == PredictedWinner.FIGHTER1),
                "fighter2": sum(1 for p in method_preds if p.predicted_winner == PredictedWinner.FIGHTER2),
            }
        
        return {
            "total_predictions": total,
            "fighter1_picks": fighter1_picks,
            "fighter2_picks": fighter2_picks,
            "fighter1_percentage": round(fighter1_picks / total * 100, 1),
            "fighter2_percentage": round(fighter2_picks / total * 100, 1),
            "methods": methods,
        }
    
    def get_fight_scorecard_stats(self, session: Session, fight_id: int) -> Dict[str, Any]:
        """Get aggregated scorecard statistics for a fight.
        
        Returns:
            Dict with average scores per round and winner consensus.
        """
        scorecards = self.get_scorecards_for_fight(session, fight_id)
        total = len(scorecards)
        
        if total == 0:
            return {
                "total_scorecards": 0,
                "rounds": {},
                "average_total_fighter1": 0,
                "average_total_fighter2": 0,
                "fighter1_wins": 0,
                "fighter2_wins": 0,
                "draws": 0,
                "fighter1_win_percentage": 0,
                "fighter2_win_percentage": 0,
            }
        
        # Get the fight to know number of rounds
        fight = session.get(Fight, fight_id)
        num_rounds = fight.rounds or 3
        
        # Aggregate round scores
        rounds: Dict[int, Dict[str, float]] = {}
        for round_num in range(1, num_rounds + 1):
            round_scores = []
            for sc in scorecards:
                for rs in sc.round_scores:
                    if rs.round_number == round_num:
                        round_scores.append((rs.fighter1_score, rs.fighter2_score))
                        break
            
            if round_scores:
                avg_f1 = sum(s[0] for s in round_scores) / len(round_scores)
                avg_f2 = sum(s[1] for s in round_scores) / len(round_scores)
                rounds[round_num] = {
                    "average_fighter1": round(avg_f1, 2),
                    "average_fighter2": round(avg_f2, 2),
                    "fighter1_round_wins": sum(1 for s in round_scores if s[0] > s[1]),
                    "fighter2_round_wins": sum(1 for s in round_scores if s[1] > s[0]),
                }
        
        # Count overall winners
        fighter1_wins = sum(1 for sc in scorecards if sc.winner == "fighter1")
        fighter2_wins = sum(1 for sc in scorecards if sc.winner == "fighter2")
        draws = sum(1 for sc in scorecards if sc.winner == "draw")
        
        # Average totals
        avg_total_f1 = sum(sc.total_fighter1 for sc in scorecards) / total
        avg_total_f2 = sum(sc.total_fighter2 for sc in scorecards) / total
        
        return {
            "total_scorecards": total,
            "rounds": rounds,
            "average_total_fighter1": round(avg_total_f1, 1),
            "average_total_fighter2": round(avg_total_f2, 1),
            "fighter1_wins": fighter1_wins,
            "fighter2_wins": fighter2_wins,
            "draws": draws,
            "fighter1_win_percentage": round(fighter1_wins / total * 100, 1),
            "fighter2_win_percentage": round(fighter2_wins / total * 100, 1),
        }
    
    def get_user_stats(self, session: Session, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        predictions = self.get_user_predictions(session, user_id)
        scorecards = self.get_user_scorecards(session, user_id)
        
        return {
            "total_predictions": len(predictions),
            "total_scorecards": len(scorecards),
            "predictions_by_method": {
                method.value: sum(1 for p in predictions if p.win_method == method)
                for method in WinMethod
            },
        }
    
    def get_fight_by_id(self, session: Session, fight_id: int) -> Optional[Fight]:
        """Get fight by ID."""
        return session.get(Fight, fight_id)

