"""Comprehensive script to scrape ALL fighter profiles and populate database"""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm

from database import Database
from database.models import Fighter
from scraper.client import HTTPClient
from scraper.parsers import FighterProfileParser, generate_fighter_profile_url
from sqlalchemy import select

console = Console()


def scrape_all_fighters(
    skip_scraped: bool = True,
    max_fighters: int = None,
    delay: float = 1.5,
    start_from: int = 0
):
    """Scrape profile data for all fighters.
    
    Args:
        skip_scraped: Skip fighters that are already marked as scraped
        max_fighters: Maximum number of fighters to process (None = all)
        delay: Delay between requests in seconds
        start_from: Skip first N fighters (for resuming)
    """
    db = Database("mma_data.db")
    client = HTTPClient()
    
    with db.get_session() as session:
        # Build query
        stmt = select(Fighter)
        
        if skip_scraped:
            stmt = stmt.where(Fighter.profile_scraped == False)
        
        stmt = stmt.order_by(Fighter.id)
        
        if start_from > 0:
            stmt = stmt.offset(start_from)
        
        if max_fighters:
            stmt = stmt.limit(max_fighters)
        
        fighters = list(session.execute(stmt).scalars().all())
        
        if not fighters:
            console.print("[yellow]No fighters to process[/yellow]")
            return
        
        console.print(f"\n[bold blue]Processing {len(fighters)} fighters[/bold blue]")
        console.print(f"[dim]Delay between requests: {delay}s[/dim]\n")
        
        success_count = 0
        error_count = 0
        not_found_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("✓{task.fields[success]} ✗{task.fields[errors]} ⊘{task.fields[not_found]}"),
            console=console
        ) as progress:
            task = progress.add_task(
                "[cyan]Scraping...", 
                total=len(fighters),
                success=0,
                errors=0,
                not_found=0
            )
            
            for i, fighter in enumerate(fighters):
                progress.update(
                    task, 
                    description=f"[cyan]{fighter.name[:40]}..."
                )
                
                try:
                    # Generate or use existing profile URL
                    if not fighter.profile_url:
                        fighter.profile_url = generate_fighter_profile_url(fighter.name)
                    
                    profile_url = fighter.profile_url
                    
                    # Fetch profile page
                    html = client.get_fighter_profile(profile_url)
                    
                    if not html:
                        not_found_count += 1
                        progress.update(task, not_found=not_found_count)
                        progress.advance(task)
                        time.sleep(delay * 0.5)  # Shorter delay for 404s
                        continue
                    
                    # Parse profile data
                    parser = FighterProfileParser(html, fighter.name)
                    profile_data = parser.parse_profile()
                    
                    if not profile_data:
                        error_count += 1
                        progress.update(task, errors=error_count)
                        progress.advance(task)
                        time.sleep(delay)
                        continue
                    
                    # Track what was updated
                    updated_fields = []
                    
                    # Update all available fields
                    if profile_data.name_english and profile_data.name_english != fighter.name:
                        fighter.name_english = profile_data.name_english
                        updated_fields.append("en_name")
                    
                    if profile_data.country:
                        fighter.country = profile_data.country
                        updated_fields.append("country")
                    
                    if profile_data.age:
                        fighter.age = profile_data.age
                        updated_fields.append("age")
                    
                    if profile_data.height_cm:
                        fighter.height_cm = profile_data.height_cm
                        updated_fields.append("height")
                    
                    if profile_data.weight_kg:
                        fighter.weight_kg = profile_data.weight_kg
                        updated_fields.append("weight")
                    
                    if profile_data.reach_cm:
                        fighter.reach_cm = profile_data.reach_cm
                        updated_fields.append("reach")
                    
                    if profile_data.style:
                        fighter.style = profile_data.style
                        updated_fields.append("style")
                    
                    if profile_data.ranking:
                        fighter.ranking = profile_data.ranking
                        updated_fields.append("ranking")
                    
                    # Always update win/loss methods
                    fighter.wins_ko_tko = profile_data.wins_ko_tko or 0
                    fighter.wins_submission = profile_data.wins_submission or 0
                    fighter.wins_decision = profile_data.wins_decision or 0
                    fighter.losses_ko_tko = profile_data.losses_ko_tko or 0
                    fighter.losses_submission = profile_data.losses_submission or 0
                    fighter.losses_decision = profile_data.losses_decision or 0
                    updated_fields.append("methods")
                    
                    # Update record if it changed
                    if (profile_data.wins != fighter.wins or 
                        profile_data.losses != fighter.losses or 
                        profile_data.draws != fighter.draws):
                        fighter.wins = profile_data.wins
                        fighter.losses = profile_data.losses
                        fighter.draws = profile_data.draws
                        updated_fields.append("record")
                    
                    # Mark as scraped
                    fighter.profile_scraped = True
                    
                    session.commit()
                    success_count += 1
                    progress.update(task, success=success_count)
                    
                    if len(updated_fields) > 0:
                        console.print(f"[green]✓ {fighter.name}: {', '.join(updated_fields)}[/green]")
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupted! Progress saved.[/yellow]")
                    session.commit()
                    raise
                    
                except Exception as e:
                    error_msg = str(e)[:80]
                    console.print(f"[red]✗ {fighter.name}: {error_msg}[/red]")
                    error_count += 1
                    progress.update(task, errors=error_count)
                    session.rollback()
                
                progress.advance(task)
                time.sleep(delay)
        
        console.print(f"\n[bold]Final Results:[/bold]")
        console.print(f"[green]✓ Successfully scraped: {success_count}/{len(fighters)}[/green]")
        console.print(f"[red]✗ Errors/Parse failures: {error_count}[/red]")
        console.print(f"[yellow]⊘ Not found (404): {not_found_count}[/yellow]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape ALL fighter profiles from gidstats.com"
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
        help="Delay between requests in seconds (default: 1.5, recommended: 1.5-2.0)"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Skip first N fighters (useful for resuming)"
    )
    parser.add_argument(
        "--include-scraped",
        action="store_true",
        help="Re-scrape fighters that were already scraped (updates their data)"
    )
    
    args = parser.parse_args()
    
    # Show summary
    db = Database("mma_data.db")
    with db.get_session() as session:
        stmt = select(Fighter)
        if not args.include_scraped:
            stmt = stmt.where(Fighter.profile_scraped == False)
        total = len(list(session.execute(stmt).scalars().all()))
    
    console.print(f"\n[bold]Fighters to process: {total}[/bold]")
    
    if total == 0:
        console.print("[yellow]No fighters need scraping![/yellow]")
        exit(0)
    
    if total > 100 and not args.max:
        estimated_time = (total * args.delay) / 60
        console.print(f"[yellow]Estimated time: ~{estimated_time:.0f} minutes[/yellow]")
        console.print(f"[dim]Tip: Use --max 50 to test with a smaller batch first[/dim]\n")
        
        if not Confirm.ask(f"Proceed with scraping {total} fighters?"):
            console.print("[yellow]Cancelled[/yellow]")
            exit(0)
    
    try:
        scrape_all_fighters(
            skip_scraped=not args.include_scraped,
            max_fighters=args.max,
            delay=args.delay,
            start_from=args.start_from
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()

