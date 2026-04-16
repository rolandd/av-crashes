import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
from datetime import datetime

DMV_URL = "https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/"


def parse_date_and_company(date_text: str) -> Dict[str, str]:
    """
    Parses date_text like 'Waymo LLC - 03/23/26'
    Returns {'company': company_name, 'date': formatted_date}
    """
    try:
        if " - " in date_text:
            company, date_part = date_text.split(" - ", 1)
            # Remove LLC, Inc, etc.
            company = (
                company.replace(" LLC", "")
                .replace(" Inc.", "")
                .replace(" Inc", "")
                .strip()
            )

            # Parse date 03/23/26 -> 2026-03-23
            dt = datetime.strptime(date_part.strip(), "%m/%d/%y")
            formatted_date = dt.strftime("%Y-%m-%d")
            return {"company": company, "date": formatted_date}
    except Exception as e:
        logging.error(f"Failed to parse date_text '{date_text}': {e}")

    return {"company": "AV Collision", "date": datetime.now().strftime("%Y-%m-%d")}


def fetch_collision_reports() -> List[Dict[str, Any]]:
    """
    Fetches the DMV collision reports page and parses out PDF URLs and their dates.
    Returns a list of dicts containing {url, date_text, company, date}.
    """
    logging.info(f"Fetching DMV page: {DMV_URL}")
    response = requests.get(DMV_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    reports = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/file/" in href and (href.endswith(".pdf/") or href.endswith("-pdf/")):
            # Extract date if possible from link text or nearby context.
            # Link text often looks like "Waymo LLC - 03/23/26" or similar.
            text = link.get_text(strip=True)

            # Use absolute URL
            if not href.startswith("http"):
                href = f"https://www.dmv.ca.gov{href}"

            parsed = parse_date_and_company(text)
            reports.append(
                {
                    "url": href,
                    "date_text": text,
                    "company": parsed["company"],
                    "date": parsed["date"],
                }
            )

    return reports
