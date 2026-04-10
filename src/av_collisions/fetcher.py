import requests
from bs4 import BeautifulSoup
from typing import List, Tuple
import logging

DMV_URL = "https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/"

def fetch_collision_reports() -> List[Tuple[str, str]]:
    """
    Fetches the DMV collision reports page and parses out PDF URLs and their dates.
    Returns a list of tuples containing (url, date_string).
    """
    logging.info(f"Fetching DMV page: {DMV_URL}")
    response = requests.get(DMV_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    reports = []

    # Common pattern for DMV portal: PDFs are in links within tables or list items.
    # The user provided an example: https://www.dmv.ca.gov/portal/file/waymo_032326_redacted-pdf/
    # Often the date is in the link text or a preceding table cell.
    
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/file/" in href and (href.endswith(".pdf/") or href.endswith("-pdf/")):
            # Extract date if possible from link text or nearby context.
            # Link text often looks like "Waymo LLC - 03/23/26" or similar.
            text = link.get_text(strip=True)
            
            # Use absolute URL
            if not href.startswith("http"):
                href = f"https://www.dmv.ca.gov{href}"
            
            reports.append((href, text))

    return reports
