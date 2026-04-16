import logging
import os
import re
from datetime import datetime
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


def main():
    """Main orchestration loop."""
    logging.info("Starting AV Collisions Scraper")

    # Ensure data directories exist
    os.makedirs("data/images", exist_ok=True)
    os.makedirs("data/metadata", exist_ok=True)

    # 1. Load state
    state = load_state()

    # 2. Fetch reports from DMV
    try:
        reports = fetch_collision_reports()
        logging.info(f"Found {len(reports)} collision reports on DMV site.")
    except Exception as e:
        logging.error(f"Failed to fetch reports: {e}")
        return

    # 3. Process new reports
    newly_processed = 0
    for url, date_text in reports:
        if is_processed(state, url):
            continue

        logging.info(f"Processing new report: {url} ({date_text})")

        try:
            # Download and parse PDF
            pdf_bytes = download_pdf(url)
            image_bytes, description, extra_metadata = extract_section_5(pdf_bytes)

            if image_bytes:
                # Save results
                filename_base = slugify(url)
                image_path = save_output(
                    image_bytes, description, filename_base, url, extra_metadata
                )

                # Post to Bluesky
                post_to_bluesky(url, date_text, image_path, extra_metadata, description)

                # Mark as processed in state
                metadata = {
                    "url": url,
                    "date_text": date_text,
                    "processed_at": datetime.now().isoformat(),
                    "filename_base": filename_base,
                }
                mark_processed(state, url, metadata)
                newly_processed += 1
            else:
                logging.warning(f"Could not find Section 5 in PDF: {url}")

        except Exception as e:
            logging.error(f"Error processing {url}: {e}")
            continue

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
