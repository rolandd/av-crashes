import os
import logging
from atproto import Client, models, client_utils  # type: ignore[import-untyped]
from typing import Dict, Any


def post_to_bluesky(
    url: str,
    company: str,
    formatted_date: str,
    image_bytes: bytes,
    metadata: Dict[str, Any],
    description_text: str,
) -> None:
    """
    Posts a collision report to Bluesky.
    """
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_PASSWORD")

    if not handle or not password:
        logging.warning("Bluesky credentials not set. Skipping post.")
        return

    # Determine autonomous mode status
    status = "yes" if metadata.get("autonomous_mode") else "no"

    # Build post text using TextBuilder for robust facets
    text_builder = client_utils.TextBuilder()
    text_builder.link(f"{company} {formatted_date}", url)
    text_builder.text(f":\n  autonomous mode: {status}")

    logging.info(f"Posting to Bluesky: {text_builder.build_text()}")

    try:
        client = Client()
        client.login(handle, password)

        # Upload image
        upload = client.upload_blob(image_bytes)

        # Create the post embed
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

        client.send_post(text=text_builder, embed=embed)
        logging.info("Successfully posted to Bluesky.")

    except Exception as e:
        logging.error(f"Error posting to Bluesky: {e}")
