# CLI Modes and Storage Refactor Plan

## Objective
Update the AV Collision scraper to support a "bootstrap" mode for initializing state, a "local test" mode for processing specific URLs, and eliminate the persistent storage of generated images and metadata in the `data/` directory during normal execution.

## Key Files & Context
- `src/av_collisions/main.py`: Needs `argparse` integration, logic for the new modes, and refactoring to handle temporary image storage for Bluesky.
- `src/av_collisions/pdf_parser.py`: Needs updates to how `save_output` is used, potentially modifying it to support outputting to the current directory or a temporary directory.
- `src/av_collisions/bluesky.py`: Needs to handle posting from temporary files.
- `.github/workflows/daily-scrape.yml`: Needs to be updated to no longer commit files in the `data/` directory.

## Implementation Steps

### 1. Refactor PDF Output Handling (`src/av_collisions/pdf_parser.py`)
- Modify `save_output` to accept a destination directory rather than hardcoding `data/images` and `data/metadata`.
- Alternatively, return the `image_bytes` and let `main.py` handle writing it to disk. (Currently, `extract_section_5` already returns `image_bytes`). We can simplify the "save" step in `main.py`.

### 2. Implement CLI Arguments (`src/av_collisions/main.py`)
- Import `argparse`.
- Add `--bootstrap`: A boolean flag to run the bootstrap mode.
- Add `--url`: An optional string argument to run the local test mode for a specific report URL.

### 3. Implement Bootstrap Mode
- When `--bootstrap` is passed:
  - Fetch all reports from the DMV.
  - Iterate through them.
  - If a report is not in `state.json`, mark it as processed with basic metadata (url, date_text, company, date, processed_at).
  - Do NOT download the PDFs or post to Bluesky.
  - Save the updated `state.json`.

### 4. Implement Local Test Mode
- When `--url <URL>` is passed:
  - Bypass the DMV fetch.
  - Call `download_pdf` and `extract_section_5` for the provided URL.
  - Save the extracted image (`.png`) and metadata (`.json`) directly to the current working directory (`.`).
  - Do NOT update `state.json`.
  - Do NOT post to Bluesky.

### 5. Refactor Normal Mode (Default)
- When no flags are passed:
  - Fetch reports from the DMV.
  - For each new report:
    - Download and parse the PDF.
    - Write the image to a *temporary file* (using the `tempfile` module).
    - Post to Bluesky using the temporary image file.
    - Update `state.json`.
    - Do NOT write to `data/images` or `data/metadata`.

### 6. Update GitHub Action (`.github/workflows/daily-scrape.yml`)
- Modify the `Commit and push changes` step.
- Update the `file_pattern` to only include `state.json`. Remove the references to `data/images/*.png` and `data/metadata/*.json`.

## Verification
- Test `--bootstrap` locally to ensure it populates `state.json` without errors.
- Test `--url <some_pdf_url>` to ensure it writes the `.png` and `.json` to the current directory.
- Test a normal run to ensure it uses temporary files and correctly processes state.