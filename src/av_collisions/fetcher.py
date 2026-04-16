import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
import re
from datetime import datetime

DMV_URL = "https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/"


def parse_date_and_company(date_text: str) -> Dict[str, str] | None:
    """
    Parses date_text from DMV collision reports page.
    Handles formats like:
    - 'Waymo March 23, 2026 (PDF)'
    - 'Waymo December 29. 2022 (PDF)'
    - 'Waymo LLC - 03/23/26'
    Returns {'company': company_name, 'date': formatted_date} or None if not a report.
    """
    # Skip known noise
    lower_text = date_text.lower()
    noise_keywords = [
        "submit a collision",
        "accident-involving-an-autonomous-vehicle",
        "traffic accident involving",
    ]
    if any(k in lower_text for k in noise_keywords):
        return None

    # 1. Try "Company Month Day, Year (PDF)" format
    # Allow . or , after the day
    match = re.search(r"^(.*?)\s+([A-Z][a-z]+)\s+(\d{1,2})[.,]?\s+(\d{4})", date_text)
    if match:
        company = match.group(1).strip()
        month_str = match.group(2)
        day_str = match.group(3)
        year_str = match.group(4)

        try:
            dt = datetime.strptime(f"{month_str} {day_str} {year_str}", "%B %d %Y")
            return {
                "company": company,
                "date": dt.strftime("%Y-%m-%d"),
            }
        except ValueError:
            pass

    # 2. Try old format "Company - MM/DD/YY"
    if " - " in date_text:
        try:
            company, date_part = date_text.split(" - ", 1)
            # Remove (PDF) if present in old format
            date_part = date_part.replace("(PDF)", "").strip()
            # Remove LLC, Inc, etc.
            company = (
                company.replace(" LLC", "")
                .replace(" Inc.", "")
                .replace(" Inc", "")
                .strip()
            )

            # Parse date 03/23/26 -> 2026-03-23
            dt = datetime.strptime(date_part, "%m/%d/%y")
            return {
                "company": company,
                "date": dt.strftime("%Y-%m-%d"),
            }
        except Exception:
            pass

    # Final check: if it looks like a report but parsing failed, we could return a fallback,
    # but for bootstrap accuracy it's better to be strict.
    # If the first word is a known company or the string contains a year, we might try harder,
    # but returning None here will filter out "Autonomous Vehicle Collision Reports" etc.
    return None


def fetch_collision_reports() -> List[Dict[str, Any]]:
    """
    Fetches the DMV collision reports page and parses out PDF URLs and their dates.
    Returns a list of dicts containing {url, raw_title, company, date}.
    """
    logging.info(f"Fetching DMV page: {DMV_URL}")
    response = requests.get(DMV_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    reports = []

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/file/" in href and (href.endswith(".pdf/") or href.endswith("-pdf/")):
            text = link.get_text(strip=True)

            parsed = parse_date_and_company(text)
            if not parsed:
                continue

            # Use absolute URL
            if not href.startswith("http"):
                href = f"https://www.dmv.ca.gov{href}"

            reports.append(
                {
                    "url": href,
                    "raw_title": text,
                    "company": parsed["company"],
                    "date": parsed["date"],
                }
            )

    return reports
