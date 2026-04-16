import logging
import re
import argparse
from datetime import datetime
from typing import Dict, Any
from .fetcher import fetch_collision_reports
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
) -> bool | None:
    """
    Processes a single report: downloads, parses, and optionally posts.
    Returns the autonomous_mode status boolean if successful, else None.
    """
    url = report["url"]
    raw_title = report["raw_title"]
    company = report["company"]
    date = report["date"]

    logging.info(f"Processing report: {url} ({raw_title})")

    try:
        # Download and parse PDF
        pdf_bytes = download_pdf(url)
        image_bytes, description, extra_metadata = extract_section_5(pdf_bytes)

        if image_bytes:
            slug = slugify(url)
            # Add fetched info to metadata
            extra_metadata["company"] = company
            extra_metadata["date"] = date
            extra_metadata["raw_title"] = raw_title

            if save_dir:
                # Save to specific directory (e.g., current dir for local test)
                save_output(
                    image_bytes,
                    description,
                    slug,
                    url,
                    extra_metadata,
                    save_dir,
                )
                logging.info(f"Saved output to {save_dir}")

            if post:
                post_to_bluesky(
                    url, company, date, image_bytes, extra_metadata, description
                )
            return bool(extra_metadata.get("autonomous_mode"))
        else:
            logging.warning(f"Could not find Section 5 in PDF: {url}")
            return None

    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return None


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
            "raw_title": "Local Test Mode",
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
        logging.info("Running in bootstrap mode. Filling/updating state.")
        newly_marked = 0
        today_str = datetime.now().strftime("%Y-%m-%d")

        for report in reports:
            url = report["url"]
            existing_meta = state.get("processed_urls", {}).get(url, {})

            # Update if:
            # 1. Not in state
            # 2. Missing company info
            # 3. Uses fallback "AV Collision"
            # 4. Has today's date (indicating fallback from previous run) but report is older
            needs_update = (
                not is_processed(state, url)
                or "company" not in existing_meta
                or existing_meta.get("company") == "AV Collision"
                or (
                    existing_meta.get("date") == today_str
                    and report["date"] != today_str
                )
            )

            if needs_update:
                metadata = {
                    "raw_title": report["raw_title"],
                    "company": report["company"],
                    "date": report["date"],
                    "processed_at": datetime.now().isoformat(),
                    "bootstrapped": True,
                }
                mark_processed(state, url, metadata)
                newly_marked += 1

        # Optional: Remove entries from state.json that are no longer on the DMV site
        # This keeps the bootstrap clean if we want a 1:1 mapping.
        # But we might want to keep history. Let's just filter out the "Submit" ones manually if they linger.
        # Actually, let's just purge known noise URLs from state if they exist.
        noise_urls = [
            u
            for u in state.get("processed_urls", {})
            if "submit-a-collision" in u
            or "accident-involving-an-autonomous-vehicle" in u
        ]
        for u in noise_urls:
            logging.info(f"Removing noise URL from state: {u}")
            del state["processed_urls"][u]
            newly_marked += 1

        if newly_marked > 0:
            logging.info(f"Bootstrapped/Updated {newly_marked} reports. Saving state.")
            save_state(state)
        else:
            logging.info("No new or missing data to bootstrap.")
        return

    # 3. Normal Mode: Process new reports
    newly_processed = 0
    for report in reports:
        url = report["url"]
        if is_processed(state, url):
            continue

        auto_mode = process_single_report(report, post=True)
        if auto_mode is not None:
            # Mark as processed in state
            metadata = {
                "raw_title": report["raw_title"],
                "company": report["company"],
                "date": report["date"],
                "autonomous_mode": auto_mode,
                "processed_at": datetime.now().isoformat(),
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
