"""HTTP client with retry logic and rate limiting for web scraping."""

import time
import random
from typing import Optional
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console

console = Console()

# User agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


def rate_limit(min_delay: float = 1.0, max_delay: float = 3.0):
    """Decorator to add random delay between requests.
    
    Args:
        min_delay: Minimum delay in seconds.
        max_delay: Maximum delay in seconds.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
            return result
        return wrapper
    return decorator


class HTTPClient:
    """HTTP client with retry logic, rate limiting, and User-Agent rotation."""
    
    BASE_URL = "https://gidstats.com"
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
    ):
        """Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries.
            backoff_factor: Backoff factor for retries.
        """
        self.timeout = timeout
        self.session = self._create_session(max_retries, backoff_factor)
        
    def _create_session(
        self,
        max_retries: int,
        backoff_factor: float,
    ) -> requests.Session:
        """Create a requests session with retry logic.
        
        Args:
            max_retries: Maximum number of retries.
            backoff_factor: Backoff factor for retries.
            
        Returns:
            Configured requests session.
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_headers(self) -> dict:
        """Get request headers with random User-Agent.
        
        Returns:
            Headers dictionary.
        """
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5,ru;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
    
    @rate_limit(min_delay=1.0, max_delay=2.5)
    def get(self, url: str, full_url: bool = False) -> Optional[str]:
        """Make a GET request with rate limiting.
        
        Args:
            url: URL path (will be appended to BASE_URL) or full URL if full_url=True.
            full_url: If True, use url as-is; otherwise prepend BASE_URL.
            
        Returns:
            Response text or None if request failed.
        """
        request_url = url if full_url else f"{self.BASE_URL}{url}"
        
        try:
            response = self.session.get(
                request_url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
            
        except requests.exceptions.Timeout:
            console.print(f"[red]✗[/red] Timeout fetching {request_url}")
            return None
            
        except requests.exceptions.HTTPError as e:
            console.print(f"[red]✗[/red] HTTP error {e.response.status_code} for {request_url}")
            return None
            
        except requests.exceptions.RequestException as e:
            console.print(f"[red]✗[/red] Request failed for {request_url}: {e}")
            return None
    
    def get_events_page(self) -> Optional[str]:
        """Fetch the events list page.
        
        Returns:
            HTML content of events page or None.
        """
        console.print("[blue]→[/blue] Fetching events list...")
        html = self.get("/ru/events")
        if html:
            console.print("[green]✓[/green] Events list fetched")
        return html
    
    def get_event_detail(self, slug: str) -> Optional[str]:
        """Fetch an individual event detail page.
        
        Args:
            slug: Event slug (e.g., "aca-197").
            
        Returns:
            HTML content of event page or None.
        """
        console.print(f"[blue]→[/blue] Fetching event: {slug}")
        html = self.get(f"/ru/events/{slug}/")
        if html:
            console.print(f"[green]✓[/green] Event fetched: {slug}")
        return html
    
    def get_fighter_profile(self, profile_url: str) -> Optional[str]:
        """Fetch a fighter's profile page.
        
        Args:
            profile_url: Full URL to fighter profile.
            
        Returns:
            HTML content of profile page or None.
        """
        html = self.get(profile_url, full_url=True)
        return html
    
    def get_rankings_page(self, organization: str = "aca") -> Optional[str]:
        """Fetch a rankings page for an organization.
        
        Args:
            organization: Organization slug (e.g., "aca", "ufc").
            
        Returns:
            HTML content of rankings page or None.
        """
        console.print(f"[blue]→[/blue] Fetching {organization.upper()} rankings...")
        html = self.get(f"/ru/ranking/{organization}/")
        if html:
            console.print(f"[green]✓[/green] Rankings fetched")
        return html
    
    def close(self) -> None:
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

