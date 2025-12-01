"""BeautifulSoup parsers for gidstats.com pages."""

import re
from datetime import date, datetime
from typing import Optional, List, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from rich.console import Console

from .validators import EventData, FightData, FighterData

console = Console()

BASE_URL = "https://gidstats.com"


class EventListParser:
    """Parser for the events list page (/ru/events)."""
    
    def __init__(self, html: str):
        """Initialize parser with HTML content.
        
        Args:
            html: HTML content of the events list page.
        """
        self.soup = BeautifulSoup(html, "lxml")
    
    def parse_upcoming_events(self) -> List[EventData]:
        """Parse upcoming events from the page.
        
        Returns:
            List of EventData objects.
        """
        events = []
        
        # Find all links to individual events
        # Pattern matches URLs like /ru/events/aca-197/ or /ru/events/pfl_mena_4-2579/
        event_links = self.soup.find_all("a", href=re.compile(r"/ru/events/[a-z0-9_-]+/?$"))
        
        seen_slugs = set()
        
        for link in event_links:
            href = link.get("href", "")
            if not href:
                continue
                
            # Extract slug from URL (handles both aca-197 and pfl_mena_4-2579 formats)
            slug_match = re.search(r"/ru/events/([a-z0-9_-]+)/?$", href)
            if not slug_match:
                continue
                
            slug = slug_match.group(1)
            
            # Skip duplicates
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            
            # Get event name from link text or parent
            name = self._extract_event_name(link, slug)
            if not name:
                continue
            
            # Try to find date and location near this link
            event_date, time_msk = self._find_event_datetime(link)
            location = self._find_event_location(link)
            
            # Extract organization from name
            organization = EventData.extract_organization(name)
            
            try:
                event = EventData(
                    name=name,
                    organization=organization,
                    slug=slug,
                    url=urljoin(BASE_URL, href),
                    event_date=event_date,
                    time_msk=time_msk,
                    location=location,
                    is_upcoming=True,
                )
                events.append(event)
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Failed to parse event {slug}: {e}")
        
        # Deduplicate by slug
        unique_events = {}
        for event in events:
            if event.slug not in unique_events:
                unique_events[event.slug] = event
        
        return list(unique_events.values())
    
    def _extract_event_name(self, link: Tag, slug: str) -> Optional[str]:
        """Extract event name from link or surrounding context.
        
        Link text format: "05.12.202517:00 МСКACA 197Moscow, Russia"
        We need to extract just "ACA 197"
        
        Args:
            link: BeautifulSoup Tag for the link.
            slug: Event slug.
            
        Returns:
            Event name or None.
        """
        text = link.get_text(strip=True)
        
        # Extract organization + event name/number pattern
        # This is the most reliable pattern
        org_patterns = [
            r'(UFC\s+(?:Vegas\s+)?\d+)',
            r'(UFC\s+\d+)',
            r'(ACA\s+Young\s+Eagles\s+\d+)',
            r'(ACA\s+\d+)',
            r'(PFL\s+(?:MENA|Europe|Africa)\s+\d+)',
            r'(PFL\s+\d+)',
            r'(PFL)',  # Just PFL for generic PFL events
            r'(KSW\s+\d+)',
            r'(OKTAGON\s+\d+)',
            r'(Cage\s+Warriors\s+\d+)',
            r'(Bellator\s+\d+)',
            r'(BRAVE\s+CF\s+\d+)',
            r'(UAE\s+Warriors\s+\d+)',
            r'(Ares\s+FC\s+\d+)',
            r'(MMA\s+Series\s+\d+)',
            r'(Open\s+FC\s+\d+)',
            r'(LFA\s+\d+)',
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: convert slug to name
        name = slug.replace("-", " ").replace("_", " ").title()
        # Clean up slug-based name
        name = re.sub(r'\s*\d{4,}$', '', name)  # Remove trailing year-like numbers
        return name
    
    def _find_event_datetime(self, link: Tag) -> Tuple[Optional[date], Optional[str]]:
        """Find event date and time near a link.
        
        Args:
            link: BeautifulSoup Tag for the link.
            
        Returns:
            Tuple of (date, time_msk).
        """
        event_date = None
        time_msk = None
        
        # Search in parent elements for date pattern
        parent = link.parent
        for _ in range(5):
            if parent:
                text = parent.get_text()
                
                # Look for date pattern DD.MM.YYYY or DD.MM.YY
                date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{2,4})", text)
                if date_match:
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    year = int(date_match.group(3))
                    if year < 100:
                        year += 2000
                    try:
                        event_date = date(year, month, day)
                    except ValueError:
                        pass
                
                # Look for time pattern HH:MM
                time_match = re.search(r"(\d{1,2}:\d{2})\s*(?:МСК)?", text)
                if time_match:
                    time_msk = time_match.group(1)
                
                if event_date and time_msk:
                    break
                    
                parent = parent.parent
        
        return event_date, time_msk
    
    def _find_event_location(self, link: Tag) -> Optional[str]:
        """Find event location from link text.
        
        Link text format: "05.12.202517:00 МСКACA 197Moscow, Russia"
        
        Args:
            link: BeautifulSoup Tag for the link.
            
        Returns:
            Location string or None.
        """
        text = link.get_text(strip=True)
        
        # Location is at the end of the link text after event name
        # Pattern: anything ending with City, Country or City, State, Country
        loc_patterns = [
            # City, State/Region, Country (e.g., "Grozny, Chechnya, Russia")
            r'([A-Za-zÀ-ž][A-Za-zÀ-ž\s]+,\s*[A-Za-zÀ-ž][A-Za-zÀ-ž\s]+,\s*[A-Za-zÀ-ž][A-Za-zÀ-ž\s]+)\.?\s*$',
            # City, Country (Latin with accents, e.g., "Moscow, Russia", "Łódź, Poland")
            r'([A-Za-zÀ-ž][A-Za-zÀ-ž\s]+,\s*[A-Za-zÀ-ž][A-Za-zÀ-ž\s]+)\.?\s*$',
            # City, Country (Cyrillic)
            r'([А-Я][а-яА-Я\s]+,\s*[А-Я][а-яА-Я\s]+)\.?\s*$',
            # Handle "UFC APEX, Las Vegas, USA" type
            r'([A-Z][A-Za-z\s]+,\s*[A-Z][a-zA-Z\s]+,\s*[A-Z][A-Za-z]+)\.?\s*$',
            # Just country name at end (e.g., "Benin.")
            r'([A-Za-zÀ-ž]{4,})\.?\s*$',
        ]
        
        for pattern in loc_patterns:
            loc_match = re.search(pattern, text)
            if loc_match:
                location = loc_match.group(1).strip().rstrip('.')
                # Remove trailing organization names
                location = re.sub(r'\s+(?:UFC|ACA|PFL|KSW|OKTAGON|Bellator|BRAVE|UAE\s+Warriors|Ares|MMA\s+Series|Young\s+Eagles).*$', '', location, flags=re.IGNORECASE)
                location = location.strip()
                # Filter out pure organization names
                skip_words = ['ufc', 'aca', 'pfl', 'ksw', 'oktagon', 'bellator', 'brave', 'ares', 'series', 'eagles', 'mena', 'africa', 'europe']
                if location.lower() in skip_words:
                    continue
                # Accept if it's a location pattern
                if len(location) > 3:
                    return location
        
        return None
    


class EventDetailParser:
    """Parser for individual event pages (/ru/events/{slug}/)."""
    
    def __init__(self, html: str, event_slug: str):
        """Initialize parser with HTML content.
        
        Args:
            html: HTML content of the event detail page.
            event_slug: Slug of the event being parsed.
        """
        self.soup = BeautifulSoup(html, "lxml")
        self.event_slug = event_slug
    
    def parse_event_details(self) -> Optional[EventData]:
        """Parse full event details including fight card.
        
        Returns:
            EventData with fights or None if parsing failed.
        """
        # Get event name from h1 or title
        name = self._get_event_name()
        if not name:
            console.print(f"[yellow]⚠[/yellow] Could not find event name for {self.event_slug}")
            name = self.event_slug.replace("-", " ").title()
        
        # Get event date and time
        event_date, time_msk = self._get_event_datetime()
        
        # Get location
        location = self._get_location()
        
        # Extract organization
        organization = EventData.extract_organization(name)
        
        # Parse fights
        fights = self._parse_fights()
        
        try:
            return EventData(
                name=name,
                organization=organization,
                slug=self.event_slug,
                url=f"{BASE_URL}/ru/events/{self.event_slug}/",
                event_date=event_date,
                time_msk=time_msk,
                location=location,
                is_upcoming=event_date >= date.today() if event_date else True,
                fights=fights,
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create EventData for {self.event_slug}: {e}")
            return None
    
    def _get_event_name(self) -> Optional[str]:
        """Get event name from page.
        
        Returns:
            Event name or None.
        """
        # Try h1 first
        h1 = self.soup.find("h1")
        if h1:
            name = h1.get_text(strip=True)
            if name:
                return name
        
        # Try title tag
        title = self.soup.find("title")
        if title:
            title_text = title.get_text(strip=True)
            # Remove site name suffix
            name = re.sub(r"\s*[-|]\s*GID\s*Stats.*$", "", title_text, flags=re.IGNORECASE)
            if name:
                return name
        
        return None
    
    def _get_event_datetime(self) -> Tuple[Optional[date], Optional[str]]:
        """Get event date and time.
        
        Returns:
            Tuple of (date, time_msk).
        """
        event_date = None
        time_msk = None
        
        # Look for date/time in the page
        text = self.soup.get_text()
        
        # Pattern: DD.MM.YY or DD.MM.YYYY
        date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{2,4})", text)
        if date_match:
            try:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3))
                if year < 100:
                    year += 2000
                event_date = date(year, month, day)
            except ValueError:
                pass
        
        # Pattern: HH:MM МСК
        time_match = re.search(r"(\d{1,2}:\d{2})\s*МСК", text)
        if time_match:
            time_msk = time_match.group(1)
        
        return event_date, time_msk
    
    def _get_location(self) -> Optional[str]:
        """Get event location.
        
        Returns:
            Location string or None.
        """
        # Look for location in page header area (first 2000 chars)
        # The location is typically near the event name and date
        text = self.soup.get_text()[:2000]
        
        # Patterns to match location after date/time
        patterns = [
            # After date and time МСК: City, Country (Latin)
            r"\d{2}\.\d{2}\.\d{2,4}\s*\d{1,2}:\d{2}\s*МСК\s*([A-Za-z][A-Za-z\s]+,\s*[A-Za-z][A-Za-z\s]+)",
            # After date and time МСК: City, Country (Cyrillic)
            r"\d{2}\.\d{2}\.\d{2,4}\s*\d{1,2}:\d{2}\s*МСК\s*([А-Яа-я][А-Яа-я\s]+,\s*[А-Яа-я][А-Яа-я\s]+)",
            # City, Country near beginning of text (Latin)
            r"^[^,]{0,200}([A-Z][a-zA-Z\s]{2,20},\s*[A-Z][a-zA-Z\s]{2,20})",
        ]
        
        for pattern in patterns:
            loc_match = re.search(pattern, text, re.MULTILINE)
            if loc_match:
                location = loc_match.group(1).strip().rstrip('.')
                if len(location) > 5 and "," in location:
                    return location
        
        return None
    
    def _parse_fights(self) -> List[FightData]:
        """Parse all fights from the event page.
        
        Returns:
            List of FightData objects.
        """
        fights = []
        
        # Find fight entries - they typically have VS between fighter names
        # Look for patterns with fighter records
        
        # Try to find main card and prelim sections
        main_fights = self._parse_card_section("main")
        prelim_fights = self._parse_card_section("prelim")
        
        fights.extend(main_fights)
        fights.extend(prelim_fights)
        
        # If no fights found in sections, try general parsing
        if not fights:
            fights = self._parse_fights_general()
        
        # Add fight order
        for i, fight in enumerate(fights):
            fight.fight_order = i
        
        return fights
    
    def _parse_card_section(self, card_type: str) -> List[FightData]:
        """Parse fights from a specific card section.
        
        Args:
            card_type: Type of card ('main' or 'prelim').
            
        Returns:
            List of FightData objects.
        """
        fights = []
        
        # Look for section headers
        section_keywords = {
            "main": ["основной кард", "main card", "основной"],
            "prelim": ["прелимы", "prelims", "preliminary", "прелиминари"],
        }
        
        keywords = section_keywords.get(card_type, [])
        
        # Find section by keyword
        for keyword in keywords:
            elements = self.soup.find_all(string=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                # Get parent container
                container = element.find_parent(["div", "section", "ul"])
                if container:
                    section_fights = self._extract_fights_from_container(container, card_type)
                    fights.extend(section_fights)
        
        return fights
    
    def _extract_fights_from_container(self, container: Tag, card_type: str) -> List[FightData]:
        """Extract fights from a container element.
        
        Args:
            container: BeautifulSoup Tag containing fights.
            card_type: Type of card.
            
        Returns:
            List of FightData objects.
        """
        fights = []
        
        # Look for list items or divs with fight info
        items = container.find_all(["li", "div", "tr"])
        
        for item in items:
            text = item.get_text()
            
            # Look for VS pattern
            if "VS" in text.upper() or " - " in text:
                fight = self._parse_fight_from_text(text, card_type)
                if fight:
                    fights.append(fight)
        
        return fights
    
    def _parse_fights_general(self) -> List[FightData]:
        """Parse fights using general pattern matching.
        
        Returns:
            List of FightData objects.
        """
        fights = []
        
        # Find containers that have exactly 2 fighter records
        # This is the structure used by gidstats.com
        items = self.soup.find_all(['li', 'div', 'tr'])
        
        for item in items:
            text = item.get_text()
            
            # Find all records in this container (W-L-D pattern)
            records = re.findall(r'(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)', text)
            
            # A fight container should have exactly 2 records
            if len(records) != 2:
                continue
            
            # Extract fighter names - they appear before records
            # Pattern: Name followed by W - L - D
            name_pattern = r'([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\s]+?)\s*\d+\s*[-–]\s*\d+\s*[-–]\s*\d+'
            names = re.findall(name_pattern, text)
            
            if len(names) < 2:
                continue
            
            # Clean up names
            fighter1_name = " ".join(names[0].split()).strip()
            fighter2_name = " ".join(names[1].split()).strip()
            
            # Skip invalid names
            if len(fighter1_name) < 3 or len(fighter2_name) < 3:
                continue
            
            # Skip if names contain unwanted text
            skip_words = ['регистрация', 'фрибет', 'кард', 'прелимы', 'основной']
            if any(w in fighter1_name.lower() for w in skip_words):
                continue
            if any(w in fighter2_name.lower() for w in skip_words):
                continue
            
            try:
                fighter1 = FighterData(
                    name=fighter1_name,
                    wins=int(records[0][0]),
                    losses=int(records[0][1]),
                    draws=int(records[0][2]),
                )
                
                fighter2 = FighterData(
                    name=fighter2_name,
                    wins=int(records[1][0]),
                    losses=int(records[1][1]),
                    draws=int(records[1][2]),
                )
                
                # Extract scheduled time if present
                time_match = re.search(r'(\d{1,2}:\d{2})\s*МСК', text)
                scheduled_time = time_match.group(1) if time_match else None
                
                # Extract rounds if present (e.g., "5 x 5" or "3 x 5")
                rounds_match = re.search(r'(\d)\s*x\s*\d', text)
                rounds = int(rounds_match.group(1)) if rounds_match else None
                
                fight = FightData(
                    fighter1=fighter1,
                    fighter2=fighter2,
                    card_type="main",
                    scheduled_time=scheduled_time,
                    rounds=rounds,
                )
                fights.append(fight)
                
            except (ValueError, IndexError) as e:
                continue
        
        # Remove duplicates (same fighters)
        seen = set()
        unique_fights = []
        for fight in fights:
            key = (fight.fighter1.name, fight.fighter2.name)
            if key not in seen:
                seen.add(key)
                unique_fights.append(fight)
        
        return unique_fights
    
    def _parse_fight_from_text(self, text: str, card_type: str) -> Optional[FightData]:
        """Parse a single fight from text.
        
        Args:
            text: Text containing fight info.
            card_type: Type of card.
            
        Returns:
            FightData or None.
        """
        # Pattern for: Name Record VS Name Record
        # Handle both Latin and Cyrillic names
        pattern = r"([A-Za-zА-Яа-яЁё\s]+?)\s*(\d+\s*[-–]\s*\d+\s*[-–]\s*\d+).*?(?:VS|vs|против).*?([A-Za-zА-Яа-яЁё\s]+?)\s*(\d+\s*[-–]\s*\d+\s*[-–]\s*\d+)"
        
        match = re.search(pattern, text)
        if not match:
            return None
        
        try:
            fighter1_name = match.group(1).strip()
            fighter1_record = match.group(2).replace(" ", "").replace("–", "-")
            fighter2_name = match.group(3).strip()
            fighter2_record = match.group(4).replace(" ", "").replace("–", "-")
            
            # Clean names
            fighter1_name = " ".join(fighter1_name.split())
            fighter2_name = " ".join(fighter2_name.split())
            
            if len(fighter1_name) < 2 or len(fighter2_name) < 2:
                return None
            
            fighter1 = FighterData.from_record_string(fighter1_name, fighter1_record)
            fighter2 = FighterData.from_record_string(fighter2_name, fighter2_record)
            
            # Try to extract scheduled time
            time_match = re.search(r"(\d{1,2}:\d{2})\s*МСК", text)
            scheduled_time = time_match.group(1) if time_match else None
            
            # Try to extract rounds
            rounds_match = re.search(r"(\d)\s*x\s*\d", text)
            rounds = int(rounds_match.group(1)) if rounds_match else None
            
            return FightData(
                fighter1=fighter1,
                fighter2=fighter2,
                card_type=card_type,
                scheduled_time=scheduled_time,
                rounds=rounds,
            )
            
        except Exception:
            return None


class FighterProfileParser:
    """Parser for individual fighter profile pages (/ru/fighters/{slug}.html)."""
    
    def __init__(self, html: str, fighter_name: str):
        """Initialize parser with HTML content.
        
        Args:
            html: HTML content of the fighter profile page.
            fighter_name: Name of the fighter being parsed.
        """
        self.soup = BeautifulSoup(html, "lxml")
        self.fighter_name = fighter_name
    
    def parse_profile(self) -> Optional[FighterData]:
        """Parse fighter profile data.
        
        Returns:
            FighterData with full stats or None if parsing failed.
        """
        try:
            # Get basic info from the stats table
            stats = self._parse_stats_table()
            
            # Get win/loss methods
            win_methods = self._parse_win_methods()
            loss_methods = self._parse_loss_methods()
            
            # Get English name if available
            name_english = self._get_english_name()
            
            # Get ranking
            ranking = self._get_ranking()
            
            return FighterData(
                name=self.fighter_name,
                name_english=name_english,
                country=stats.get('country'),
                wins=stats.get('wins', 0),
                losses=stats.get('losses', 0),
                draws=stats.get('draws', 0),
                age=stats.get('age'),
                height_cm=stats.get('height_cm'),
                weight_kg=stats.get('weight_kg'),
                reach_cm=stats.get('reach_cm'),
                style=stats.get('style'),
                ranking=ranking,
                wins_ko_tko=win_methods.get('ko_tko', 0),
                wins_submission=win_methods.get('submission', 0),
                wins_decision=win_methods.get('decision', 0),
                losses_ko_tko=loss_methods.get('ko_tko', 0),
                losses_submission=loss_methods.get('submission', 0),
                losses_decision=loss_methods.get('decision', 0),
                profile_scraped=True,
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Error parsing fighter profile {self.fighter_name}: {e}")
            return None
    
    def _parse_stats_table(self) -> dict:
        """Parse the main stats table (Справка о бойце / Данные бойца).
        
        Returns:
            Dictionary with fighter stats.
        """
        stats = {}
        
        text = self.soup.get_text()
        
        # Parse wins/losses/draws
        wins_match = re.search(r'Победы\s*(\d+)', text)
        if wins_match:
            stats['wins'] = int(wins_match.group(1))
        
        losses_match = re.search(r'Поражения\s*(\d+)', text)
        if losses_match:
            stats['losses'] = int(losses_match.group(1))
        
        draws_match = re.search(r'Ничья\s*(\d+)', text)
        if draws_match:
            stats['draws'] = int(draws_match.group(1))
        
        # Parse age
        age_match = re.search(r'Возраст\s*(\d+)', text)
        if age_match:
            stats['age'] = int(age_match.group(1))
        
        # Parse height (Рост) - format: "184 см"
        height_match = re.search(r'Рост\s*(\d+)\s*см', text)
        if height_match:
            stats['height_cm'] = int(height_match.group(1))
        
        # Parse weight (Последний вес) - format: "93 кг"
        weight_match = re.search(r'(?:Последний\s*вес|Вес)\s*(\d+(?:\.\d+)?)\s*кг', text)
        if weight_match:
            stats['weight_kg'] = float(weight_match.group(1))
        
        # Parse reach (Размах рук) - format: "184 см"
        reach_match = re.search(r'Размах\s*рук\s*(\d+)\s*см', text)
        if reach_match:
            stats['reach_cm'] = int(reach_match.group(1))
        
        # Parse style (Стиль)
        style_match = re.search(r'Стиль\s+([А-Яа-яA-Za-z\s]+?)(?:\n|Место|Представляет)', text)
        if style_match:
            stats['style'] = style_match.group(1).strip()
        
        # Parse country (Представляет страну)
        country_match = re.search(r'Представляет\s*страну\s*([А-Яа-яA-Za-z]+)', text)
        if country_match:
            stats['country'] = country_match.group(1).strip()
        else:
            # Try alternate pattern - common country names
            country_patterns = [
                'Россия', 'Russia', 'USA', 'Brazil', 'Бразилия', 
                'Таджикистан', 'Узбекистан', 'Казахстан', 'Украина',
                'Грузия', 'Армения', 'Азербайджан', 'Кыргызстан',
                'Дагестан', 'Чечня'
            ]
            for country in country_patterns:
                if country in text:
                    stats['country'] = country
                    break
        
        return stats
    
    def _parse_win_methods(self) -> dict:
        """Parse win methods (KO/TKO, Decision, Submission).
        
        Returns:
            Dictionary with win method counts.
        """
        methods = {'ko_tko': 0, 'submission': 0, 'decision': 0}
        
        text = self.soup.get_text()
        
        # Find the wins section - pattern: "KO/TKO 6 (40%)"
        # Look for patterns after "Победы" heading
        
        ko_match = re.search(r'KO/TKO\s*(\d+)', text)
        if ko_match:
            methods['ko_tko'] = int(ko_match.group(1))
        
        # РЕШ = Decision (Решение)
        decision_match = re.search(r'РЕШ\s*(\d+)', text)
        if decision_match:
            methods['decision'] = int(decision_match.group(1))
        
        # САБ = Submission (Сабмишен)
        sub_match = re.search(r'САБ\s*(\d+)', text)
        if sub_match:
            methods['submission'] = int(sub_match.group(1))
        
        return methods
    
    def _parse_loss_methods(self) -> dict:
        """Parse loss methods.
        
        Returns:
            Dictionary with loss method counts.
        """
        methods = {'ko_tko': 0, 'submission': 0, 'decision': 0}
        
        text = self.soup.get_text()
        
        # Look for the losses section
        # Pattern after "Поражения" heading
        losses_section = re.search(r'Поражения.*?KO/TKO\s*(\d+).*?РЕШ\s*(\d+).*?САБ\s*(\d+)', text, re.DOTALL)
        if losses_section:
            methods['ko_tko'] = int(losses_section.group(1))
            methods['decision'] = int(losses_section.group(2))
            methods['submission'] = int(losses_section.group(3))
        
        return methods
    
    def _get_english_name(self) -> Optional[str]:
        """Get English name if available.
        
        Returns:
            English name or None.
        """
        # Look for h2 with English name
        h2_tags = self.soup.find_all('h2')
        for h2 in h2_tags:
            text = h2.get_text(strip=True)
            # Check if it's Latin characters (English name)
            if text and re.match(r'^[A-Za-z\s]+$', text):
                return text
        
        return None
    
    def _get_ranking(self) -> Optional[str]:
        """Get fighter ranking if available.
        
        Returns:
            Ranking string or None.
        """
        text = self.soup.get_text()
        
        # Pattern: "ACA #1 LHW" or similar
        ranking_match = re.search(r'((?:ACA|UFC|PFL|Bellator)\s*#\d+\s*\w+)', text)
        if ranking_match:
            return ranking_match.group(1)
        
        return None


class RankingsParser:
    """Parser for rankings pages (/ru/ranking/{org}/)."""
    
    def __init__(self, html: str, organization: str = "ACA"):
        """Initialize parser with HTML content.
        
        Args:
            html: HTML content of the rankings page.
            organization: Organization name.
        """
        self.soup = BeautifulSoup(html, "lxml")
        self.organization = organization
    
    def parse_all_fighters(self) -> List[dict]:
        """Parse all ranked fighters from all weight classes.
        
        Returns:
            List of dicts with fighter info (name, rank, weight_class, profile_url).
        """
        fighters = []
        
        # Find all fighter links on the page
        # Links are in format /ru/fighters/{slug}.html
        fighter_links = self.soup.find_all('a', href=re.compile(r'/ru/fighters/[a-z0-9_]+\.html'))
        
        seen_urls = set()
        
        for link in fighter_links:
            href = link.get('href', '')
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            
            # Get fighter name from link text or nearby elements
            name = link.get_text(strip=True)
            if not name or len(name) < 2:
                # Try parent element
                parent = link.parent
                if parent:
                    name = parent.get_text(strip=True)
            
            # Clean name - remove rank numbers and extra text
            name = re.sub(r'^\d+\s*', '', name)  # Remove leading rank number
            name = re.sub(r'\s*(?:Чемпион|НР|\d+|\-\d+)$', '', name)  # Remove trailing info
            name = ' '.join(name.split())  # Normalize whitespace
            
            if not name or len(name) < 3:
                continue
            
            # Build full URL
            full_url = urljoin(BASE_URL, href)
            
            # Try to determine weight class from context
            weight_class = self._get_weight_class_for_link(link)
            
            # Try to get rank
            rank = self._get_rank_for_link(link)
            
            fighters.append({
                'name': name,
                'profile_url': full_url,
                'weight_class': weight_class,
                'rank': rank,
                'organization': self.organization,
            })
        
        console.print(f"[green]✓[/green] Found {len(fighters)} ranked fighters")
        return fighters
    
    def _get_weight_class_for_link(self, link: Tag) -> Optional[str]:
        """Try to determine the weight class for a fighter link.
        
        Args:
            link: BeautifulSoup Tag for the fighter link.
            
        Returns:
            Weight class name or None.
        """
        # Weight class names in Russian
        weight_classes = {
            'Тяжелый вес': 'Heavyweight',
            'Полутяжелый вес': 'Light Heavyweight',
            'Средний вес': 'Middleweight',
            'Полусредний вес': 'Welterweight',
            'Легкий вес': 'Lightweight',
            'Полулегкий вес': 'Featherweight',
            'Легчайший вес': 'Bantamweight',
            'Наилегчайший вес': 'Flyweight',
        }
        
        # Search up the DOM tree for weight class heading
        parent = link.parent
        for _ in range(10):
            if parent:
                # Look for h3 or heading with weight class
                heading = parent.find_previous(['h3', 'h2', 'h4'])
                if heading:
                    text = heading.get_text(strip=True)
                    for ru_class, en_class in weight_classes.items():
                        if ru_class in text:
                            return en_class
                parent = parent.parent
        
        return None
    
    def _get_rank_for_link(self, link: Tag) -> Optional[int]:
        """Try to get the rank number for a fighter.
        
        Args:
            link: BeautifulSoup Tag for the fighter link.
            
        Returns:
            Rank number or None.
        """
        # Look for rank in parent text
        parent = link.parent
        if parent:
            text = parent.get_text()
            # Pattern: number followed by name
            rank_match = re.search(r'\b(\d+)\s+[А-Яа-я]', text)
            if rank_match:
                return int(rank_match.group(1))
            # Check for "Чемпион" (Champion)
            if 'Чемпион' in text:
                return 0  # 0 = Champion
        
        return None


def generate_fighter_profile_url(fighter_name: str) -> str:
    """Generate the profile URL for a fighter.
    
    Args:
        fighter_name: Fighter name (can be Cyrillic or Latin).
        
    Returns:
        URL to fighter's profile page.
    """
    # Transliterate Cyrillic to Latin for URL
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    
    # Clean and normalize the name
    name = fighter_name.lower().strip()
    # Remove "кг" prefix if present
    name = re.sub(r'^кг\s+', '', name)
    
    # Split into parts (first name, last name)
    parts = name.split()
    
    # URL format is lastname_firstname (reversed)
    if len(parts) >= 2:
        # Swap first and last name
        parts = [parts[-1]] + parts[:-1]
    
    # Join with underscore
    slug = '_'.join(parts)
    
    # Transliterate
    result = []
    for char in slug:
        if char in translit_map:
            result.append(translit_map[char])
        else:
            result.append(char)
    
    slug = ''.join(result)
    
    # Clean up any special characters
    slug = re.sub(r'[^a-z0-9_]', '', slug)
    
    return f"{BASE_URL}/ru/fighters/{slug}.html"

