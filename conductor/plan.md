# Bluesky Integration Plan

## Objective
Update the `av-collisions` scraper to automatically post new autonomous vehicle collision reports to Bluesky. The post will include the company name, date, autonomous mode status, a link to the original PDF, and an image of the report's Section 5 with extracted text as alt text.

## Key Files & Context
- `pyproject.toml`: To add the `atproto` dependency.
- `.github/workflows/daily-scrape.yml`: To provide Bluesky credentials via GitHub Secrets.
- `src/av_collisions/bluesky.py`: (New file) To handle Bluesky authentication, post formatting, and API interaction using the `atproto` SDK.
- `src/av_collisions/main.py`: To integrate the Bluesky posting step after a new report is processed.

## Implementation Steps

### 1. Update Dependencies
- Modify `pyproject.toml` to add `atproto` to the `dependencies` list.

### 2. Configure GitHub Action
- Update `.github/workflows/daily-scrape.yml`.
- In the "Run scraper" step, add `env` variables for `BLUESKY_HANDLE` and `BLUESKY_PASSWORD`, mapping them to `${{ secrets.BLUESKY_HANDLE }}` and `${{ secrets.BLUESKY_PASSWORD }}`.

### 3. Create Bluesky Posting Module (`src/av_collisions/bluesky.py`)
- Implement a function `post_to_bluesky(url, date_text, image_path, metadata, description_text)`.
- **Parsing**: Extract the company name and date from `date_text` (e.g., "Waymo LLC - 03/23/26"). Convert the date to `YYYY-MM-DD` format.
- **Formatting**: Construct the post text: `"{company} {formatted_date} - autonomous mode: {status}"`. Determine the status from `metadata['autonomous_mode']`.
- **Facets**: Use `atproto`'s rich text features to create a facet over the `"{company} {formatted_date}"` portion of the text, linking it to the original `url`.
- **Image Upload**: Read the image from `image_path` and upload it to Bluesky as a blob. Attach the `description_text` as the image's alt text.
- **Posting**: Authenticate using environment variables. Send the post containing the text, facets, and the image embed. Include robust error handling to prevent the main scraper loop from crashing if a post fails.

### 4. Integrate into Main Workflow (`src/av_collisions/main.py`)
- Import `post_to_bluesky`.
- Within the loop over new reports, after successfully saving the image and metadata (and before marking as processed), call `post_to_bluesky`.
- Pass the required arguments: the original URL, the raw date string, the saved image path, the extracted metadata, and the extracted section 5 description text.

## Verification
- Review the code changes to ensure the `atproto` SDK is used correctly for rich text facets and image uploads.
- Run `uv sync` locally to ensure dependencies install correctly.
- (Manual Verification Post-Merge) Ensure the GitHub Action runs successfully and posts to the configured Bluesky account when new reports are found.