"""Pydantic models for data validation."""

import re
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


class FighterData(BaseModel):
    """Validated fighter data."""
    
    name: str = Field(..., min_length=1, max_length=255)
    name_english: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    draws: int = Field(default=0, ge=0)
    
    # Physical stats
    age: Optional[int] = Field(None, ge=0, le=100)
    height_cm: Optional[int] = Field(None, ge=100, le=250)
    weight_kg: Optional[float] = Field(None, ge=40, le=200)
    reach_cm: Optional[int] = Field(None, ge=100, le=250)
    
    # Fighting info
    style: Optional[str] = Field(None, max_length=100)
    weight_class: Optional[str] = Field(None, max_length=50)
    ranking: Optional[str] = Field(None, max_length=50)
    
    # Win methods
    wins_ko_tko: Optional[int] = Field(None, ge=0)
    wins_submission: Optional[int] = Field(None, ge=0)
    wins_decision: Optional[int] = Field(None, ge=0)
    
    # Loss methods
    losses_ko_tko: Optional[int] = Field(None, ge=0)
    losses_submission: Optional[int] = Field(None, ge=0)
    losses_decision: Optional[int] = Field(None, ge=0)
    
    profile_url: Optional[str] = Field(None, max_length=500)
    profile_scraped: bool = Field(default=False)
    
    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean and normalize fighter name."""
        # Remove extra whitespace
        v = " ".join(v.split())
        # Remove weight class prefix (кг)
        v = re.sub(r'^кг\s+', '', v)
        return v.strip()
    
    @field_validator("country")
    @classmethod
    def clean_country(cls, v: Optional[str]) -> Optional[str]:
        """Clean country name."""
        if v:
            v = v.strip()
            return v if v else None
        return None
    
    @property
    def record(self) -> str:
        """Get fighter record as string."""
        return f"{self.wins}-{self.losses}-{self.draws}"
    
    @property
    def ko_rate(self) -> Optional[float]:
        """Get KO/TKO win percentage."""
        if self.wins and self.wins_ko_tko is not None:
            return (self.wins_ko_tko / self.wins) * 100
        return None
    
    @property
    def sub_rate(self) -> Optional[float]:
        """Get submission win percentage."""
        if self.wins and self.wins_submission is not None:
            return (self.wins_submission / self.wins) * 100
        return None
    
    @classmethod
    def from_record_string(
        cls,
        name: str,
        record_str: str,
        country: Optional[str] = None,
        profile_url: Optional[str] = None,
    ) -> "FighterData":
        """Create FighterData from a record string like '9-2-0' or '9 - 2 - 0'.
        
        Args:
            name: Fighter name.
            record_str: Record string in format 'W-L-D'.
            country: Fighter's country.
            profile_url: URL to fighter's profile.
            
        Returns:
            FighterData instance.
        """
        wins, losses, draws = 0, 0, 0
        
        # Parse record string - handles '9-2-0', '9 - 2 - 0', '9-2', etc.
        record_str = record_str.replace(" ", "")
        match = re.match(r"(\d+)-(\d+)(?:-(\d+))?", record_str)
        
        if match:
            wins = int(match.group(1))
            losses = int(match.group(2))
            draws = int(match.group(3)) if match.group(3) else 0
        
        return cls(
            name=name,
            country=country,
            wins=wins,
            losses=losses,
            draws=draws,
            profile_url=profile_url,
        )


class FightData(BaseModel):
    """Validated fight data."""
    
    fighter1: FighterData
    fighter2: FighterData
    card_type: str = Field(default="main")  # main or prelim
    weight_class: Optional[str] = Field(None, max_length=100)
    rounds: Optional[int] = Field(None, ge=1, le=5)
    scheduled_time: Optional[str] = Field(None, max_length=10)
    fight_order: Optional[int] = Field(None, ge=0)
    
    @field_validator("card_type")
    @classmethod
    def validate_card_type(cls, v: str) -> str:
        """Validate and normalize card type."""
        v = v.lower().strip()
        if v in ("main", "основной", "main card", "основной кард"):
            return "main"
        elif v in ("prelim", "prelims", "preliminary", "прелимы", "прелиминари"):
            return "prelim"
        return v
    
    @field_validator("scheduled_time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format."""
        if v:
            v = v.strip()
            # Accept formats like "23:30", "23:30 МСК"
            time_match = re.match(r"(\d{1,2}:\d{2})", v)
            if time_match:
                return time_match.group(1)
        return v


class EventData(BaseModel):
    """Validated event data."""
    
    name: str = Field(..., min_length=1, max_length=255)
    organization: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=500)
    event_date: Optional[date] = None
    time_msk: Optional[str] = Field(None, max_length=10)
    location: Optional[str] = Field(None, max_length=255)
    is_upcoming: bool = True
    fights: List[FightData] = Field(default_factory=list)
    
    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean event name."""
        return " ".join(v.split()).strip()
    
    @field_validator("organization")
    @classmethod
    def clean_organization(cls, v: str) -> str:
        """Normalize organization name."""
        v = v.strip().upper()
        # Normalize common variations
        org_map = {
            "UFC": "UFC",
            "ACA": "ACA",
            "ARES FC": "ARES FC",
            "ARES": "ARES FC",
            "BELLATOR": "BELLATOR",
            "KSW": "KSW",
            "OKTAGON": "OKTAGON",
            "PFL": "PFL",
            "CAGE WARRIORS": "CAGE WARRIORS",
            "CAGE WARRIORS FC": "CAGE WARRIORS",
            "LFA": "LFA",
            "BRAVE CF": "BRAVE CF",
            "UAE WARRIORS": "UAE WARRIORS",
            "RIZIN": "RIZIN",
            "ONE": "ONE",
            "ONE FC": "ONE",
            "ONE CHAMPIONSHIP": "ONE",
        }
        return org_map.get(v, v)
    
    @field_validator("slug")
    @classmethod
    def clean_slug(cls, v: str) -> str:
        """Clean and validate slug."""
        v = v.strip().lower()
        # Remove trailing/leading slashes
        v = v.strip("/")
        return v
    
    @field_validator("time_msk")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        """Validate time format."""
        if v:
            v = v.strip()
            time_match = re.match(r"(\d{1,2}:\d{2})", v)
            if time_match:
                return time_match.group(1)
        return v
    
    @field_validator("location")
    @classmethod
    def clean_location(cls, v: Optional[str]) -> Optional[str]:
        """Clean location string."""
        if v:
            v = " ".join(v.split()).strip()
            # Remove trailing period
            v = v.rstrip(".")
            return v if v else None
        return None
    
    @classmethod
    def extract_organization(cls, event_name: str) -> str:
        """Extract organization from event name.
        
        Args:
            event_name: Full event name like 'UFC 323' or 'ACA 197'.
            
        Returns:
            Organization name.
        """
        # Common patterns
        patterns = [
            (r"^(UFC)\s*", "UFC"),
            (r"^(ACA)\s*", "ACA"),
            (r"^(PFL)\s*", "PFL"),
            (r"^(Bellator)\s*", "BELLATOR"),
            (r"^(KSW)\s*", "KSW"),
            (r"^(OKTAGON)\s*", "OKTAGON"),
            (r"^(Cage Warriors)\s*", "CAGE WARRIORS"),
            (r"^(LFA)\s*", "LFA"),
            (r"^(BRAVE CF)\s*", "BRAVE CF"),
            (r"^(UAE Warriors)\s*", "UAE WARRIORS"),
            (r"^(Ares FC)\s*", "ARES FC"),
            (r"^(RIZIN)\s*", "RIZIN"),
            (r"^(ONE)\s*", "ONE"),
            (r"^(MMA Series)\s*", "MMA SERIES"),
            (r"^(Open FC)\s*", "OPEN FC"),
        ]
        
        for pattern, org in patterns:
            if re.match(pattern, event_name, re.IGNORECASE):
                return org
        
        # Default: take first word
        return event_name.split()[0].upper() if event_name else "UNKNOWN"


class ScrapedData(BaseModel):
    """Container for all scraped data."""
    
    events: List[EventData] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_events(self) -> int:
        """Get total number of events."""
        return len(self.events)
    
    @property
    def total_fights(self) -> int:
        """Get total number of fights across all events."""
        return sum(len(e.fights) for e in self.events)
    
    @property
    def unique_fighters(self) -> int:
        """Get count of unique fighters."""
        fighters = set()
        for event in self.events:
            for fight in event.fights:
                fighters.add(fight.fighter1.name)
                fighters.add(fight.fighter2.name)
        return len(fighters)
    
    def summary(self) -> dict:
        """Get summary of scraped data."""
        return {
            "total_events": self.total_events,
            "total_fights": self.total_fights,
            "unique_fighters": self.unique_fighters,
            "scraped_at": self.scraped_at.isoformat(),
        }

