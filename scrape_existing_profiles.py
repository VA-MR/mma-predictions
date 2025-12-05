"""Script to scrape profile data for fighters that already have profile URLs"""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from database import Database
from database.models import Fighter
from scraper.client import HTTPClient
from scraper.parsers import FighterProfileParser
from sqlalchemy import select

console = Console()


def scrape_fighters_with_urls(max_fighters: int = None, delay: float = 1.5):
    """Scrape profile data for fighters that already have profile URLs.
    
    Args:
        max_fighters: Maximum number of fighters to process (None = all)
        delay: Delay between requests in seconds
    """
    db = Database("mma_data.db")
    client = HTTPClient()
    
    with db.get_session() as session:
        # Get fighters that have profile URLs but haven't been scraped
        stmt = select(Fighter).where(
            Fighter.profile_url.isnot(None),
            Fighter.profile_scraped == False
        )
        
        if max_fighters:
            stmt = stmt.limit(max_fighters)
        
        fighters = list(session.execute(stmt).scalars().all())
        
        if not fighters:
            console.print("[yellow]No fighters with URLs need scraping[/yellow]")
            return
        
        console.print(f"[blue]Found {len(fighters)} fighters with URLs to scrape[/blue]")
        
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
                "[cyan]Scraping fighters...", 
                total=len(fighters)
            )
            
            for fighter in fighters:
                progress.update(
                    task, 
                    description=f"[cyan]{fighter.name[:40]}..."
                )
                
                try:
                    # Fetch profile page
                    html = client.get_fighter_profile(fighter.profile_url)
                    
                    if not html:
                        error_count += 1
                        progress.advance(task)
                        time.sleep(delay)
                        continue
                    
                    # Parse profile data
                    parser = FighterProfileParser(html, fighter.name)
                    profile_data = parser.parse_profile()
                    
                    if not profile_data:
                        error_count += 1
                        progress.advance(task)
                        time.sleep(delay)
                        continue
                    
                    # Update fighter with profile data
                    updates = []
                    
                    if profile_data.name_english:
                        fighter.name_english = profile_data.name_english
                        updates.append(f"english_name")
                    if profile_data.country:
                        fighter.country = profile_data.country
                        updates.append(f"country")
                    if profile_data.age:
                        fighter.age = profile_data.age
                        updates.append(f"age")
                    if profile_data.height_cm:
                        fighter.height_cm = profile_data.height_cm
                        updates.append(f"height")
                    if profile_data.weight_kg:
                        fighter.weight_kg = profile_data.weight_kg
                        updates.append(f"weight")
                    if profile_data.reach_cm:
                        fighter.reach_cm = profile_data.reach_cm
                        updates.append(f"reach")
                    if profile_data.style:
                        fighter.style = profile_data.style
                        updates.append(f"style")
                    if profile_data.ranking:
                        fighter.ranking = profile_data.ranking
                        updates.append(f"ranking")
                    
                    # Update win/loss methods
                    fighter.wins_ko_tko = profile_data.wins_ko_tko or 0
                    fighter.wins_submission = profile_data.wins_submission or 0
                    fighter.wins_decision = profile_data.wins_decision or 0
                    fighter.losses_ko_tko = profile_data.losses_ko_tko or 0
                    fighter.losses_submission = profile_data.losses_submission or 0
                    fighter.losses_decision = profile_data.losses_decision or 0
                    updates.append(f"methods")
                    
                    # Update record if changed
                    if profile_data.wins != fighter.wins or profile_data.losses != fighter.losses or profile_data.draws != fighter.draws:
                        fighter.wins = profile_data.wins
                        fighter.losses = profile_data.losses
                        fighter.draws = profile_data.draws
                        updates.append(f"record")
                    
                    # Mark as scraped
                    fighter.profile_scraped = True
                    
                    session.commit()
                    success_count += 1
                    
                    console.print(f"[green]✓ {fighter.name} - Updated: {', '.join(updates)}[/green]")
                    
                except Exception as e:
                    console.print(f"[red]✗ {fighter.name}: {str(e)[:100]}[/red]")
                    error_count += 1
                    session.rollback()
                
                progress.advance(task)
                time.sleep(delay)
        
        console.print(f"\n[bold]Results:[/bold]")
        console.print(f"[green]✓ Successfully scraped: {success_count}[/green]")
        console.print(f"[red]✗ Errors: {error_count}[/red]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape fighter profiles for fighters with existing URLs"
    )
    parser.add_argument(
        "--max",
        type=int,
        help="Maximum number of fighters to process (default: all)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between requests in seconds (default: 1.5)"
    )
    
    args = parser.parse_args()
    
    try:
        scrape_fighters_with_urls(
            max_fighters=args.max,
            delay=args.delay
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")

