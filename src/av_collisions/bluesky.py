import os
import logging
from datetime import datetime
from atproto import Client, models
from typing import Dict, Any


def parse_date_and_company(date_text: str):
    """
    Parses date_text like 'Waymo LLC - 03/23/26'
    Returns (company_name, formatted_date)
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
            return company, formatted_date
    except Exception as e:
        logging.error(f"Failed to parse date_text '{date_text}': {e}")

    return "AV Collision", datetime.now().strftime("%Y-%m-%d")


def post_to_bluesky(
    url: str,
    date_text: str,
    image_path: str,
    metadata: Dict[str, Any],
    description_text: str,
):
    """
    Posts a collision report to Bluesky.
    """
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not handle or not password:
        logging.warning("Bluesky credentials not set. Skipping post.")
        return

    company, formatted_date = parse_date_and_company(date_text)

    # Determine autonomous mode status
    auto_val = metadata.get("autonomous_mode", "/Off")
    status = "yes" if auto_val != "/Off" else "no"

    # Build post text
    link_text = f"{company} {formatted_date}"
    post_text = f"{link_text} - autonomous mode: {status}"

    logging.info(f"Posting to Bluesky: {post_text}")

    try:
        client = Client()
        client.login(handle, password)

        # Upload image
        with open(image_path, "rb") as f:
            img_data = f.read()

        upload = client.upload_blob(img_data)

        # Create facets for the link
        # The link_text is at the start of post_text
        facet = models.AppBskyRichtextFacet.Main(
            index=models.AppBskyRichtextFacet.ByteStartEnd(
                byteStart=0, byteEnd=len(link_text.encode("utf-8"))
            ),
            features=[models.AppBskyRichtextFacet.Link(uri=url)],
        )

        # Create the post
        embed = models.AppBskyEmbedImages.Main(
            images=[
                models.AppBskyEmbedImages.Image(
                    alt=description_text[
                        :2000
                    ],  # Alt text limit is usually large but let's be safe
                    image=upload.blob,
                )
            ]
        )

        client.send_post(text=post_text, facets=[facet], embed=embed)
        logging.info("Successfully posted to Bluesky.")

    except Exception as e:
        logging.error(f"Error posting to Bluesky: {e}")
