#!/usr/bin/env python3
"""
MMA Event Scraper - Main entry point.

Scrapes upcoming MMA events from gidstats.com, validates the data,
and stores it in a SQLite database.

Usage:
    python main.py                  # Full scrape of all upcoming events
    python main.py --stats          # Show database statistics
    python main.py --list           # List all events in database
    python main.py --event ACA-197  # Scrape specific event only
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from scraper import HTTPClient, EventListParser, EventDetailParser, FighterProfileParser, RankingsParser, generate_fighter_profile_url
from scraper.validators import EventData, ScrapedData
from database import Database, Fighter

console = Console()


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   MMA EVENT SCRAPER                          ║
║            Scraping gidstats.com for MMA data                ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner.strip(), style="bold blue"))


def scrape_events_list(client: HTTPClient) -> List[EventData]:
    """Scrape the events list page.
    
    Args:
        client: HTTP client instance.
        
    Returns:
        List of EventData objects.
    """
    html = client.get_events_page()
    if not html:
        console.print("[red]✗[/red] Failed to fetch events page")
        return []
    
    parser = EventListParser(html)
    events = parser.parse_upcoming_events()
    
    console.print(f"[green]✓[/green] Found {len(events)} upcoming events")
    return events


def scrape_event_details(
    client: HTTPClient,
    event: EventData,
) -> Optional[EventData]:
    """Scrape detailed event information including fight card.
    
    Args:
        client: HTTP client instance.
        event: Basic event data from events list.
        
    Returns:
        Updated EventData with fights or None if failed.
    """
    html = client.get_event_detail(event.slug)
    if not html:
        return None
    
    parser = EventDetailParser(html, event.slug)
    detailed_event = parser.parse_event_details()
    
    if detailed_event:
        # Merge data - keep list data if detail page is missing info
        if not detailed_event.event_date and event.event_date:
            detailed_event.event_date = event.event_date
        if not detailed_event.time_msk and event.time_msk:
            detailed_event.time_msk = event.time_msk
        if not detailed_event.location and event.location:
            detailed_event.location = event.location
            
        console.print(
            f"[green]✓[/green] Parsed {len(detailed_event.fights)} fights for {event.name}"
        )
        return detailed_event
    
    return event


def save_to_database(db: Database, events: List[EventData]) -> dict:
    """Save scraped events to database.
    
    Args:
        db: Database instance.
        events: List of EventData to save.
        
    Returns:
        Dictionary with save statistics.
    """
    stats = {
        "events_saved": 0,
        "fights_saved": 0,
        "fighters_saved": 0,
    }
    
    with db.get_session() as session:
        for event_data in events:
            try:
                # Create or update event
                event = db.get_or_create_event(
                    session=session,
                    name=event_data.name,
                    organization=event_data.organization,
                    slug=event_data.slug,
                    url=event_data.url,
                    event_date=event_data.event_date,
                    time_msk=event_data.time_msk,
                    location=event_data.location,
                    is_upcoming=event_data.is_upcoming,
                )
                stats["events_saved"] += 1
                
                # Clear existing fights for this event (we'll re-add them)
                db.clear_fights_for_event(session, event.id)
                
                # Add fights
                for fight_data in event_data.fights:
                    # Create or update fighters
                    fighter1 = db.get_or_create_fighter(
                        session=session,
                        name=fight_data.fighter1.name,
                        country=fight_data.fighter1.country,
                        wins=fight_data.fighter1.wins,
                        losses=fight_data.fighter1.losses,
                        draws=fight_data.fighter1.draws,
                        profile_url=fight_data.fighter1.profile_url,
                    )
                    stats["fighters_saved"] += 1
                    
                    fighter2 = db.get_or_create_fighter(
                        session=session,
                        name=fight_data.fighter2.name,
                        country=fight_data.fighter2.country,
                        wins=fight_data.fighter2.wins,
                        losses=fight_data.fighter2.losses,
                        draws=fight_data.fighter2.draws,
                        profile_url=fight_data.fighter2.profile_url,
                    )
                    stats["fighters_saved"] += 1
                    
                    # Create fight
                    db.create_fight(
                        session=session,
                        event=event,
                        fighter1=fighter1,
                        fighter2=fighter2,
                        card_type=fight_data.card_type,
                        weight_class=fight_data.weight_class,
                        rounds=fight_data.rounds,
                        scheduled_time=fight_data.scheduled_time,
                        fight_order=fight_data.fight_order,
                    )
                    stats["fights_saved"] += 1
                
                session.commit()
                
            except Exception as e:
                console.print(f"[red]✗[/red] Error saving {event_data.name}: {e}")
                session.rollback()
    
    return stats


def validate_scraped_data(events: List[EventData]) -> tuple:
    """Validate scraped data and report issues.
    
    Args:
        events: List of EventData to validate.
        
    Returns:
        Tuple of (valid_events, error_messages).
    """
    valid_events = []
    errors = []
    
    for event in events:
        event_errors = []
        
        # Check required fields
        if not event.name:
            event_errors.append(f"Event missing name (slug: {event.slug})")
        if not event.organization:
            event_errors.append(f"Event {event.name} missing organization")
        
        # Check date is valid
        if event.event_date and event.event_date.year < 2020:
            event_errors.append(f"Event {event.name} has suspicious date: {event.event_date}")
        
        # Check fights
        for fight in event.fights:
            if not fight.fighter1.name or not fight.fighter2.name:
                event_errors.append(f"Fight in {event.name} missing fighter name")
            
            # Check for unrealistic records
            for fighter in [fight.fighter1, fight.fighter2]:
                total_fights = fighter.wins + fighter.losses + fighter.draws
                if total_fights > 100:
                    event_errors.append(
                        f"Fighter {fighter.name} has unrealistic record: {fighter.record}"
                    )
        
        if event_errors:
            errors.extend(event_errors)
        else:
            valid_events.append(event)
    
    return valid_events, errors


def display_events_table(db: Database):
    """Display all events in a table."""
    with db.get_session() as session:
        events = db.get_all_events(session)
        
        if not events:
            console.print("[yellow]No events in database[/yellow]")
            return
        
        table = Table(title="MMA Events")
        table.add_column("ID", style="dim")
        table.add_column("Date", style="cyan")
        table.add_column("Event", style="bold")
        table.add_column("Organization", style="magenta")
        table.add_column("Location")
        table.add_column("Fights", justify="right")
        
        for event in events:
            fights_count = len(event.fights)
            date_str = event.event_date.strftime("%Y-%m-%d") if event.event_date else "TBD"
            
            table.add_row(
                str(event.id),
                date_str,
                event.name,
                event.organization,
                event.location or "TBD",
                str(fights_count),
            )
        
        console.print(table)


def display_stats(db: Database):
    """Display database statistics."""
    with db.get_session() as session:
        stats = db.get_stats(session)
        
        table = Table(title="Database Statistics")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right", style="cyan")
        
        table.add_row("Total Events", str(stats["total_events"]))
        table.add_row("Upcoming Events", str(stats["upcoming_events"]))
        table.add_row("Total Fighters", str(stats["total_fighters"]))
        table.add_row("Total Fights", str(stats["total_fights"]))
        
        console.print(table)


def run_scraper(event_slug: Optional[str] = None, limit: Optional[int] = None):
    """Run the full scraping pipeline.
    
    Args:
        event_slug: Optional specific event slug to scrape.
        limit: Optional limit on number of events to scrape.
    """
    print_banner()
    start_time = datetime.now()
    
    # Initialize database
    db_path = Path(__file__).parent / "mma_data.db"
    db = Database(str(db_path))
    db.create_tables()
    
    console.print()
    console.print("[bold]Starting scraper...[/bold]")
    console.print()
    
    with HTTPClient() as client:
        if event_slug:
            # Scrape single event
            console.print(f"[blue]→[/blue] Scraping single event: {event_slug}")
            
            # Create a basic event data object
            from scraper.validators import EventData
            basic_event = EventData(
                name=event_slug.replace("-", " ").title(),
                organization=EventData.extract_organization(event_slug.replace("-", " ").title()),
                slug=event_slug,
                url=f"https://gidstats.com/ru/events/{event_slug}/",
            )
            
            detailed_event = scrape_event_details(client, basic_event)
            events = [detailed_event] if detailed_event else []
        else:
            # Scrape all upcoming events
            console.print("[blue]→[/blue] Fetching upcoming events list...")
            events = scrape_events_list(client)
            
            if limit:
                events = events[:limit]
                console.print(f"[yellow]⚠[/yellow] Limited to {limit} events")
            
            # Get detailed info for each event
            console.print()
            console.print("[blue]→[/blue] Fetching event details...")
            
            detailed_events = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Scraping events...", total=len(events))
                
                for event in events:
                    progress.update(task, description=f"Scraping {event.name}...")
                    detailed = scrape_event_details(client, event)
                    if detailed:
                        detailed_events.append(detailed)
                    progress.advance(task)
            
            events = detailed_events
    
    console.print()
    
    # Validate data
    console.print("[blue]→[/blue] Validating scraped data...")
    valid_events, errors = validate_scraped_data(events)
    
    if errors:
        console.print(f"[yellow]⚠[/yellow] Found {len(errors)} validation issues:")
        for error in errors[:5]:  # Show first 5 errors
            console.print(f"   • {error}")
        if len(errors) > 5:
            console.print(f"   ... and {len(errors) - 5} more")
    else:
        console.print("[green]✓[/green] All data validated successfully")
    
    # Save to database
    console.print()
    console.print("[blue]→[/blue] Saving to database...")
    save_stats = save_to_database(db, valid_events)
    
    # Summary
    duration = datetime.now() - start_time
    
    console.print()
    console.print(Panel(
        f"""
[bold green]Scraping Complete![/bold green]

Events scraped:  {len(valid_events)}
Fights saved:    {save_stats['fights_saved']}
Fighters saved:  {save_stats['fighters_saved']}

Duration: {duration.total_seconds():.1f} seconds
Database: {db_path}
        """.strip(),
        title="Summary",
        style="green",
    ))


def scrape_rankings(organization: str = "aca", limit: Optional[int] = None):
    """Scrape all fighters from an organization's rankings page.
    
    Args:
        organization: Organization to scrape (e.g., "aca", "ufc").
        limit: Optional limit on number of profiles to scrape.
    """
    print_banner()
    start_time = datetime.now()
    
    db_path = Path(__file__).parent / "mma_data.db"
    db = Database(str(db_path))
    db.create_tables()
    
    console.print()
    console.print(f"[bold]Scraping {organization.upper()} Rankings...[/bold]")
    console.print()
    
    stats = {"found": 0, "scraped": 0, "failed": 0}
    
    with HTTPClient() as client:
        # Fetch rankings page
        html = client.get_rankings_page(organization)
        if not html:
            console.print("[red]✗[/red] Failed to fetch rankings page")
            return
        
        # Parse rankings to get all fighters
        parser = RankingsParser(html, organization.upper())
        ranked_fighters = parser.parse_all_fighters()
        stats["found"] = len(ranked_fighters)
        
        if limit:
            ranked_fighters = ranked_fighters[:limit]
            console.print(f"[yellow]⚠[/yellow] Limited to {limit} fighters")
        
        console.print()
        console.print(f"[blue]→[/blue] Scraping {len(ranked_fighters)} fighter profiles...")
        console.print()
        
        with db.get_session() as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Scraping profiles...", total=len(ranked_fighters))
                
                for fighter_info in ranked_fighters:
                    name = fighter_info['name']
                    profile_url = fighter_info['profile_url']
                    weight_class = fighter_info.get('weight_class')
                    rank = fighter_info.get('rank')
                    
                    progress.update(task, description=f"Scraping {name}...")
                    
                    # Fetch profile
                    html = client.get_fighter_profile(profile_url)
                    
                    if not html:
                        stats["failed"] += 1
                        progress.advance(task)
                        continue
                    
                    # Parse profile
                    profile_parser = FighterProfileParser(html, name)
                    profile_data = profile_parser.parse_profile()
                    
                    if profile_data:
                        # Build ranking string
                        if rank == 0:
                            ranking_str = f"{organization.upper()} Champion {weight_class or ''}"
                        elif rank:
                            ranking_str = f"{organization.upper()} #{rank} {weight_class or ''}"
                        else:
                            ranking_str = None
                        
                        # Create or update fighter
                        db.get_or_create_fighter(
                            session=session,
                            name=name,
                            name_english=profile_data.name_english,
                            country=profile_data.country,
                            wins=profile_data.wins,
                            losses=profile_data.losses,
                            draws=profile_data.draws,
                            age=profile_data.age,
                            height_cm=profile_data.height_cm,
                            weight_kg=profile_data.weight_kg,
                            reach_cm=profile_data.reach_cm,
                            style=profile_data.style,
                            ranking=ranking_str,
                            wins_ko_tko=profile_data.wins_ko_tko,
                            wins_submission=profile_data.wins_submission,
                            wins_decision=profile_data.wins_decision,
                            losses_ko_tko=profile_data.losses_ko_tko,
                            losses_submission=profile_data.losses_submission,
                            losses_decision=profile_data.losses_decision,
                            profile_url=profile_url,
                            profile_scraped=True,
                        )
                        stats["scraped"] += 1
                    else:
                        stats["failed"] += 1
                    
                    progress.advance(task)
            
            session.commit()
    
    duration = datetime.now() - start_time
    
    console.print()
    console.print(Panel(
        f"""
[bold green]Rankings Scraping Complete![/bold green]

Fighters found:   {stats['found']}
Profiles scraped: {stats['scraped']}
Failed:           {stats['failed']}

Duration: {duration.total_seconds():.1f} seconds
        """.strip(),
        title="Summary",
        style="green",
    ))


def scrape_fighter_profiles(limit: Optional[int] = None):
    """Scrape detailed fighter profiles for fighters in the database.
    
    Args:
        limit: Optional limit on number of profiles to scrape.
    """
    print_banner()
    start_time = datetime.now()
    
    db_path = Path(__file__).parent / "mma_data.db"
    db = Database(str(db_path))
    db.create_tables()
    
    console.print()
    console.print("[bold]Scraping fighter profiles...[/bold]")
    console.print()
    
    stats = {"scraped": 0, "failed": 0, "skipped": 0}
    
    with db.get_session() as session:
        # Get fighters without scraped profiles
        fighters = db.get_fighters_without_profiles(session)
        
        if not fighters:
            console.print("[yellow]No fighters need profile scraping[/yellow]")
            return
        
        if limit:
            fighters = fighters[:limit]
            
        console.print(f"[blue]→[/blue] Found {len(fighters)} fighters to scrape")
        console.print()
        
        with HTTPClient() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Scraping profiles...", total=len(fighters))
                
                for fighter in fighters:
                    progress.update(task, description=f"Scraping {fighter.name}...")
                    
                    # Generate profile URL
                    profile_url = generate_fighter_profile_url(fighter.name)
                    
                    # Fetch profile
                    html = client.get_fighter_profile(profile_url)
                    
                    if not html:
                        stats["failed"] += 1
                        progress.advance(task)
                        continue
                    
                    # Parse profile
                    parser = FighterProfileParser(html, fighter.name)
                    profile_data = parser.parse_profile()
                    
                    if profile_data:
                        # Update fighter with profile data
                        fighter.name_english = profile_data.name_english
                        fighter.country = profile_data.country
                        fighter.age = profile_data.age
                        fighter.height_cm = profile_data.height_cm
                        fighter.weight_kg = profile_data.weight_kg
                        fighter.reach_cm = profile_data.reach_cm
                        fighter.style = profile_data.style
                        fighter.ranking = profile_data.ranking
                        fighter.wins_ko_tko = profile_data.wins_ko_tko
                        fighter.wins_submission = profile_data.wins_submission
                        fighter.wins_decision = profile_data.wins_decision
                        fighter.losses_ko_tko = profile_data.losses_ko_tko
                        fighter.losses_submission = profile_data.losses_submission
                        fighter.losses_decision = profile_data.losses_decision
                        fighter.profile_url = profile_url
                        fighter.profile_scraped = True
                        
                        stats["scraped"] += 1
                    else:
                        stats["failed"] += 1
                    
                    progress.advance(task)
                
                session.commit()
    
    duration = datetime.now() - start_time
    
    console.print()
    console.print(Panel(
        f"""
[bold green]Profile Scraping Complete![/bold green]

Profiles scraped: {stats['scraped']}
Failed:           {stats['failed']}

Duration: {duration.total_seconds():.1f} seconds
        """.strip(),
        title="Summary",
        style="green",
    ))


def display_fighter_stats(db: Database, fighter_name: str):
    """Display detailed stats for a specific fighter."""
    with db.get_session() as session:
        fighter = db.get_fighter_by_name(session, fighter_name)
        
        if not fighter:
            console.print(f"[red]Fighter '{fighter_name}' not found[/red]")
            return
        
        # Build stats panel
        stats_text = f"""
[bold cyan]{fighter.name}[/bold cyan]
"""
        if fighter.name_english:
            stats_text += f"[dim]{fighter.name_english}[/dim]\n"
        
        if fighter.ranking:
            stats_text += f"[yellow]{fighter.ranking}[/yellow]\n"
        
        stats_text += f"""
[bold]Record:[/bold] {fighter.wins}-{fighter.losses}-{fighter.draws}
"""
        
        if fighter.age:
            stats_text += f"[bold]Age:[/bold] {fighter.age}\n"
        if fighter.height_cm:
            stats_text += f"[bold]Height:[/bold] {fighter.height_cm} cm\n"
        if fighter.weight_kg:
            stats_text += f"[bold]Weight:[/bold] {fighter.weight_kg} kg\n"
        if fighter.reach_cm:
            stats_text += f"[bold]Reach:[/bold] {fighter.reach_cm} cm\n"
        if fighter.style:
            stats_text += f"[bold]Style:[/bold] {fighter.style}\n"
        if fighter.country:
            stats_text += f"[bold]Country:[/bold] {fighter.country}\n"
        
        if fighter.wins_ko_tko is not None or fighter.wins_submission is not None:
            stats_text += f"""
[bold green]Win Methods:[/bold green]
  KO/TKO:     {fighter.wins_ko_tko or 0}
  Submission: {fighter.wins_submission or 0}
  Decision:   {fighter.wins_decision or 0}
"""
        
        if fighter.losses > 0 and (fighter.losses_ko_tko or fighter.losses_submission or fighter.losses_decision):
            stats_text += f"""
[bold red]Loss Methods:[/bold red]
  KO/TKO:     {fighter.losses_ko_tko or 0}
  Submission: {fighter.losses_submission or 0}
  Decision:   {fighter.losses_decision or 0}
"""
        
        console.print(Panel(stats_text.strip(), title="🥊 Fighter Profile"))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MMA Event Scraper - Scrape gidstats.com for MMA event data"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display database statistics",
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all events in database",
    )
    
    parser.add_argument(
        "--event",
        type=str,
        help="Scrape a specific event by slug (e.g., aca-197)",
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of events/profiles to scrape",
    )
    
    parser.add_argument(
        "--profiles",
        action="store_true",
        help="Scrape detailed fighter profiles for fighters in database",
    )
    
    parser.add_argument(
        "--fighter",
        type=str,
        help="Display stats for a specific fighter",
    )
    
    parser.add_argument(
        "--rankings",
        type=str,
        nargs='?',
        const='aca',
        help="Scrape all fighters from rankings page (default: aca)",
    )
    
    args = parser.parse_args()
    
    # Initialize database for stats/list commands
    db_path = Path(__file__).parent / "mma_data.db"
    db = Database(str(db_path))
    
    if args.stats:
        db.create_tables()
        display_stats(db)
    elif args.list:
        db.create_tables()
        display_events_table(db)
    elif args.profiles:
        # Scrape fighter profiles
        try:
            scrape_fighter_profiles(limit=args.limit)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scraping interrupted by user[/yellow]")
            sys.exit(1)
    elif args.rankings:
        # Scrape rankings page
        try:
            scrape_rankings(organization=args.rankings, limit=args.limit)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scraping interrupted by user[/yellow]")
            sys.exit(1)
    elif args.fighter:
        db.create_tables()
        display_fighter_stats(db, args.fighter)
    else:
        # Run scraper
        try:
            run_scraper(event_slug=args.event, limit=args.limit)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scraping interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            raise


if __name__ == "__main__":
    main()

