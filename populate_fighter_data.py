"""Script to populate missing fighter profile data from gidstats.com"""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from database import Database
from database.models import Fighter
from scraper.client import HTTPClient
from scraper.parsers import FighterProfileParser, generate_fighter_profile_url
from sqlalchemy import select

console = Console()


def populate_all_fighters(max_fighters: int = None, delay: float = 1.0):
    """Populate profile data for all fighters in the database.
    
    Args:
        max_fighters: Maximum number of fighters to process (None = all)
        delay: Delay between requests in seconds to avoid overloading the server
    """
    db = Database("mma_data.db")
    client = HTTPClient()
    
    with db.get_session() as session:
        # Get all fighters that haven't had their profiles scraped
        stmt = select(Fighter).where(Fighter.profile_scraped == False)
        
        if max_fighters:
            stmt = stmt.limit(max_fighters)
        
        fighters = list(session.execute(stmt).scalars().all())
        
        if not fighters:
            console.print("[yellow]No fighters need profile scraping[/yellow]")
            return
        
        console.print(f"[blue]Found {len(fighters)} fighters to process[/blue]")
        
        success_count = 0
        error_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Processing fighters...", 
                total=len(fighters)
            )
            
            for fighter in fighters:
                progress.update(
                    task, 
                    description=f"[cyan]Processing: {fighter.name[:30]}..."
                )
                
                try:
                    # Generate profile URL
                    if fighter.profile_url:
                        profile_url = fighter.profile_url
                    else:
                        profile_url = generate_fighter_profile_url(fighter.name)
                        fighter.profile_url = profile_url
                    
                    # Fetch profile page
                    html = client.get_fighter_profile(profile_url)
                    
                    if not html:
                        console.print(f"[yellow]⚠ No HTML for {fighter.name}[/yellow]")
                        error_count += 1
                        progress.advance(task)
                        continue
                    
                    # Parse profile data
                    parser = FighterProfileParser(html, fighter.name)
                    profile_data = parser.parse_profile()
                    
                    if not profile_data:
                        console.print(f"[yellow]⚠ Failed to parse {fighter.name}[/yellow]")
                        error_count += 1
                        progress.advance(task)
                        continue
                    
                    # Update fighter with profile data
                    if profile_data.name_english:
                        fighter.name_english = profile_data.name_english
                    if profile_data.country:
                        fighter.country = profile_data.country
                    if profile_data.age:
                        fighter.age = profile_data.age
                    if profile_data.height_cm:
                        fighter.height_cm = profile_data.height_cm
                    if profile_data.weight_kg:
                        fighter.weight_kg = profile_data.weight_kg
                    if profile_data.reach_cm:
                        fighter.reach_cm = profile_data.reach_cm
                    if profile_data.style:
                        fighter.style = profile_data.style
                    if profile_data.ranking:
                        fighter.ranking = profile_data.ranking
                    
                    # Update win methods
                    fighter.wins_ko_tko = profile_data.wins_ko_tko or 0
                    fighter.wins_submission = profile_data.wins_submission or 0
                    fighter.wins_decision = profile_data.wins_decision or 0
                    
                    # Update loss methods
                    fighter.losses_ko_tko = profile_data.losses_ko_tko or 0
                    fighter.losses_submission = profile_data.losses_submission or 0
                    fighter.losses_decision = profile_data.losses_decision or 0
                    
                    # Mark as scraped
                    fighter.profile_scraped = True
                    
                    session.commit()
                    success_count += 1
                    
                    console.print(f"[green]✓ {fighter.name}[/green]")
                    
                except Exception as e:
                    console.print(f"[red]✗ Error with {fighter.name}: {e}[/red]")
                    error_count += 1
                    session.rollback()
                
                progress.advance(task)
                
                # Delay to avoid overloading the server
                time.sleep(delay)
        
        console.print(f"\n[bold green]✓ Complete![/bold green]")
        console.print(f"[green]Success: {success_count}[/green]")
        console.print(f"[red]Errors: {error_count}[/red]")


def populate_specific_fighter(fighter_name: str):
    """Populate profile data for a specific fighter.
    
    Args:
        fighter_name: Name of the fighter to update
    """
    db = Database("mma_data.db")
    client = HTTPClient()
    
    with db.get_session() as session:
        stmt = select(Fighter).where(Fighter.name == fighter_name)
        fighter = session.execute(stmt).scalar_one_or_none()
        
        if not fighter:
            console.print(f"[red]Fighter '{fighter_name}' not found[/red]")
            return
        
        console.print(f"[blue]Processing fighter: {fighter.name}[/blue]")
        
        try:
            # Generate profile URL
            if fighter.profile_url:
                profile_url = fighter.profile_url
            else:
                profile_url = generate_fighter_profile_url(fighter.name)
                fighter.profile_url = profile_url
            
            console.print(f"[cyan]Profile URL: {profile_url}[/cyan]")
            
            # Fetch profile page
            html = client.get_fighter_profile(profile_url)
            
            if not html:
                console.print(f"[red]Failed to fetch profile page[/red]")
                return
            
            # Parse profile data
            parser = FighterProfileParser(html, fighter.name)
            profile_data = parser.parse_profile()
            
            if not profile_data:
                console.print(f"[red]Failed to parse profile[/red]")
                return
            
            # Update fighter with profile data
            console.print("\n[yellow]Updating fields:[/yellow]")
            
            if profile_data.name_english:
                fighter.name_english = profile_data.name_english
                console.print(f"  English Name: {profile_data.name_english}")
            if profile_data.country:
                fighter.country = profile_data.country
                console.print(f"  Country: {profile_data.country}")
            if profile_data.age:
                fighter.age = profile_data.age
                console.print(f"  Age: {profile_data.age}")
            if profile_data.height_cm:
                fighter.height_cm = profile_data.height_cm
                console.print(f"  Height: {profile_data.height_cm} cm")
            if profile_data.weight_kg:
                fighter.weight_kg = profile_data.weight_kg
                console.print(f"  Weight: {profile_data.weight_kg} kg")
            if profile_data.reach_cm:
                fighter.reach_cm = profile_data.reach_cm
                console.print(f"  Reach: {profile_data.reach_cm} cm")
            if profile_data.style:
                fighter.style = profile_data.style
                console.print(f"  Style: {profile_data.style}")
            if profile_data.ranking:
                fighter.ranking = profile_data.ranking
                console.print(f"  Ranking: {profile_data.ranking}")
            
            # Update win/loss methods
            fighter.wins_ko_tko = profile_data.wins_ko_tko or 0
            fighter.wins_submission = profile_data.wins_submission or 0
            fighter.wins_decision = profile_data.wins_decision or 0
            fighter.losses_ko_tko = profile_data.losses_ko_tko or 0
            fighter.losses_submission = profile_data.losses_submission or 0
            fighter.losses_decision = profile_data.losses_decision or 0
            
            console.print(f"\n  Win Methods: KO/TKO={fighter.wins_ko_tko}, Sub={fighter.wins_submission}, Dec={fighter.wins_decision}")
            console.print(f"  Loss Methods: KO/TKO={fighter.losses_ko_tko}, Sub={fighter.losses_submission}, Dec={fighter.losses_decision}")
            
            # Mark as scraped
            fighter.profile_scraped = True
            
            session.commit()
            
            console.print(f"\n[bold green]✓ Successfully updated {fighter.name}![/bold green]")
            
        except Exception as e:
            console.print(f"[red]✗ Error: {e}[/red]")
            session.rollback()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate fighter profile data")
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Process all fighters"
    )
    parser.add_argument(
        "--fighter",
        type=str,
        help="Process specific fighter by name"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of fighters to process"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    if args.fighter:
        populate_specific_fighter(args.fighter)
    elif args.all or args.max:
        populate_all_fighters(max_fighters=args.max, delay=args.delay)
    else:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  Process all fighters: python3 populate_fighter_data.py --all")
        console.print("  Process 10 fighters:  python3 populate_fighter_data.py --max 10")
        console.print("  Process one fighter:  python3 populate_fighter_data.py --fighter 'Абдурахман Юсупов'")

