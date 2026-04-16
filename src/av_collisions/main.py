import logging
import os
import re
import argparse
import tempfile
from datetime import datetime
from typing import Dict, Any
from .fetcher import fetch_collision_reports, parse_date_and_company
from .pdf_parser import download_pdf, extract_section_5, save_output
from .state_manager import load_state, save_state, is_processed, mark_processed
from .bluesky import post_to_bluesky

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def slugify(value: str) -> str:
    """Simplified slugify to create safe filenames from URLs."""
    # Extract filename from URL (e.g., waymo_032326_redacted-pdf/)
    # Remove protocol, host, etc.
    name = value.split("/")[-2] if value.endswith("/") else value.split("/")[-1]
    name = name.replace("-pdf", "").replace(".pdf", "")
    # Remove any non-alphanumeric characters except underscore/hyphen
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", name)


def process_single_report(
    report: Dict[str, Any],
    post: bool = True,
    save_dir: str | None = None,
) -> bool:
    """Processes a single report: downloads, parses, and optionally posts."""
    url = report["url"]
    date_text = report["date_text"]
    company = report["company"]
    date = report["date"]

    logging.info(f"Processing report: {url} ({date_text})")

    try:
        # Download and parse PDF
        pdf_bytes = download_pdf(url)
        image_bytes, description, extra_metadata = extract_section_5(pdf_bytes)

        if image_bytes:
            filename_base = slugify(url)
            # Add fetched info to metadata
            extra_metadata["company"] = company
            extra_metadata["date"] = date
            extra_metadata["date_text"] = date_text

            if save_dir:
                # Save to specific directory (e.g., current dir for local test)
                save_output(
                    image_bytes,
                    description,
                    filename_base,
                    url,
                    extra_metadata,
                    save_dir,
                )
                logging.info(f"Saved output to {save_dir}")

            if post:
                # Use a temporary file for posting
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(image_bytes)
                    tmp_path = tmp.name

                try:
                    post_to_bluesky(
                        url, company, date, tmp_path, extra_metadata, description
                    )
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            return True
        else:
            logging.warning(f"Could not find Section 5 in PDF: {url}")
            return False

    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return False


def main() -> None:
    """Main orchestration loop."""
    parser = argparse.ArgumentParser(description="AV Collision Scraper")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Bootstrap state with all existing reports",
    )
    parser.add_argument(
        "--url", type=str, help="Process a specific report URL for local testing"
    )
    args = parser.parse_args()

    # 1. Load state
    state = load_state()

    if args.url:
        logging.info(f"Running in local test mode for URL: {args.url}")
        # Local test mode: bypass state, save to current dir, don't post
        report = {
            "url": args.url,
            "date_text": "Local Test Mode",
            "company": "LocalTest",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        process_single_report(report, post=False, save_dir=".")
        return

    # 2. Fetch reports from DMV
    try:
        reports = fetch_collision_reports()
        logging.info(f"Found {len(reports)} collision reports on DMV site.")
    except Exception as e:
        logging.error(f"Failed to fetch reports: {e}")
        return

    if args.bootstrap:
        logging.info("Running in bootstrap mode. Filling state without processing.")
        newly_marked = 0
        for report in reports:
            url = report["url"]
            if not is_processed(state, url):
                metadata = {
                    "url": url,
                    "date_text": report["date_text"],
                    "company": report["company"],
                    "date": report["date"],
                    "processed_at": datetime.now().isoformat(),
                    "bootstrapped": True,
                }
                mark_processed(state, url, metadata)
                newly_marked += 1

        if newly_marked > 0:
            logging.info(f"Bootstrapped {newly_marked} reports. Saving state.")
            save_state(state)
        else:
            logging.info("No new reports to bootstrap.")
        return

    # 3. Normal Mode: Process new reports
    newly_processed = 0
    for report in reports:
        url = report["url"]
        if is_processed(state, url):
            continue

        if process_single_report(report, post=True):
            # Mark as processed in state
            metadata = {
                "url": url,
                "date_text": report["date_text"],
                "company": report["company"],
                "date": report["date"],
                "processed_at": datetime.now().isoformat(),
                "filename_base": slugify(url),
            }
            mark_processed(state, url, metadata)
            newly_processed += 1

    # 4. Save updated state
    if newly_processed > 0:
        logging.info(
            f"Successfully processed {newly_processed} new reports. Saving state."
        )
        save_state(state)
    else:
        logging.info("No new reports found or processed.")


if __name__ == "__main__":
    main()
