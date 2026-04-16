# Bluesky Image Aspect Ratio Plan

## Objective
Fix the "grey space" (letterboxing) issue on Bluesky by providing the exact aspect ratio (width and height) of the extracted images. This allows the Bluesky client to size the image container correctly for the content.

## Key Files & Context
- `src/av_collisions/pdf_parser.py`: Where images are generated.
- `src/av_collisions/bluesky.py`: Where images are posted.
- `src/av_collisions/main.py`: The orchestrator that passes data between them.

## Implementation Steps

### 1. Update `src/av_collisions/pdf_parser.py`
- Modify `extract_section_5` to return the width and height of the generated pixmap.
- Update the return type hint to `Tuple[Optional[bytes], int, int, str, Dict[str, Any]]`.
- Return `(image_bytes, pix.width, pix.height, description_text, extra_metadata)`.

### 2. Update `src/av_collisions/bluesky.py`
- Modify `post_to_bluesky` signature to accept `width: int` and `height: int`.
- Update the `models.AppBskyEmbedImages.Image` constructor to include the `aspect_ratio` field.
- Use `models.AppBskyEmbedDefs.AspectRatio(width=width, height=height)`.

### 3. Update `src/av_collisions/main.py`
- Update `process_single_report` to receive the width and height from `extract_section_5`.
- Pass these dimensions to `post_to_bluesky`.

## Verification
- Run `uv run ruff check` and `uv run mypy` to ensure all signatures match.
- Run a local test with `--url` to ensure the logic still functions correctly.
