import trafilatura
from typing import Optional

def scrape_url(url: str) -> Optional[str]:
    """
    Scrape the full text content of a given URL using trafilatura.
    Handles errors gracefully and returns None if scraping fails.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return None
        
        # Extract the text content
        text = trafilatura.extract(downloaded)
        return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
