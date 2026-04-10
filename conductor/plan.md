# AV Collisions Extractor Plan

## Objective
Automate the daily extraction of collision reports from the CA DMV Autonomous Vehicles portal. The script will fetch the DMV page, identify new collision report PDFs, extract "Section 5 - Accident Details" as both an image and text using PyMuPDF, and update a checked-in state file. The process is orchestrated via a modular Python script managed by `uv` and runs daily using GitHub Actions.

## Project Structure
- `.github/workflows/daily-scrape.yml`: GitHub Action for daily execution.
- `pyproject.toml` & `uv.lock`: Project definition using `uv`.
- `src/av_collisions/main.py`: Main orchestration script.
- `src/av_collisions/fetcher.py`: BeautifulSoup-based HTML scraping logic.
- `src/av_collisions/pdf_parser.py`: PyMuPDF (fitz) logic for rendering the PDF and extracting text/images.
- `src/av_collisions/state_manager.py`: Handling `state.json` updates and reading.
- `state.json`: A file tracking the processed collision report URLs/dates.
- `data/images/`: Output folder for Section 5 screenshots.
- `data/metadata/`: Companion JSON/markdown files containing the description (alt text) for each image.

## Implementation Steps

1. **Environment Setup:**
   - Initialize the project with `uv init`.
   - Add dependencies: `requests`, `beautifulsoup4`, `pymupdf`.
   - Create the source directory structure.

2. **State Management (`state_manager.py`):**
   - Implement functions to load `state.json` into a dictionary/set of processed URLs.
   - Implement functions to save the updated state back to disk.

3. **HTML Fetcher (`fetcher.py`):**
   - Fetch the DMV page (`https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/`).
   - Use BeautifulSoup to parse the HTML, identifying links ending in `.pdf` and extracting their associated dates (e.g., from link text or nearby table cells).

4. **PDF Parser (`pdf_parser.py`):**
   - Download the PDF from the URL.
   - Open the PDF using `fitz` (PyMuPDF).
   - Search for the text "SECTION 5 — ACCIDENT DETAILS - DESCRIPTION".
   - Determine the bounding box for Section 5 and render it to a high-quality image (`.png` or `.jpg`).
   - Extract the text from this section to serve as the alt text.

5. **Orchestration (`main.py`):**
   - Load the current state.
   - Fetch the list of available reports.
   - Iterate over new reports:
     - Parse the PDF to extract the Section 5 image and text.
     - Save the image to `data/images/` using a slugified URL or date-based filename.
     - Save a companion metadata file in `data/metadata/` with the alt text.
     - Mark the URL as processed in the state.
   - Persist the updated `state.json`.

6. **GitHub Action (`daily-scrape.yml`):**
   - Set up a cron schedule (e.g., `0 8 * * *`).
   - Checkout the repository.
   - Use `astral-sh/setup-uv` to install `uv` and Python.
   - Run `uv run src/av_collisions/main.py`.
   - Use `stefanzweifel/git-auto-commit-action` (or equivalent `git` commands) to commit changes to `state.json`, `data/images/`, and `data/metadata/`.

## Verification & Testing
- Write a basic unit test (`tests/test_parser.py`) for the PDF extraction logic using a mock or downloaded test PDF.
- Run the script locally to ensure `state.json` populates correctly and images are saved before pushing the GitHub Action.