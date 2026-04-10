# AV Collisions Extractor

Automates the daily extraction of autonomous vehicle collision reports from the California DMV.

## Features
- Fetches the [DMV AV Collision Reports](https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/) page.
- Identifies new reports based on a `state.json` file.
- Downloads collision report PDFs.
- Extracts an image of "Section 5 - Accident Details" and its text description (for alt text).
- Stores data in `data/images/` and `data/metadata/`.
- Runs daily via GitHub Actions.

## Setup
Requires [uv](https://github.com/astral-sh/uv).

```bash
uv sync
uv run src/av_collisions/main.py
```

## Structure
- `src/av_collisions/`: Source code.
- `state.json`: Tracking processed reports.
- `data/`: Extracted images and metadata.
- `.github/workflows/`: Automation.
