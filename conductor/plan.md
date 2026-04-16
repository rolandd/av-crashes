# Fetcher and Parser Refinement Plan

## Objective
1. Improve the robustness of `parse_date_and_company` to handle variations in the DMV link text format (like `.` instead of `,`).
2. Filter out noisy links (like "Submit a collision report") that are not actual reports.
3. Update `state.json` to correct the mis-parsed entries.

## Key Files & Context
- `src/av_collisions/fetcher.py`: The `parse_date_and_company` regex and the `fetch_collision_reports` loop.
- `src/av_collisions/main.py`: The `--bootstrap` logic for updating state.

## Implementation Steps

### 1. Refine `parse_date_and_company` (`src/av_collisions/fetcher.py`)
- Update the regex to handle both `.` and `,` as delimiters after the day.
- Return `None` for the date if it's truly unparseable, rather than falling back to `datetime.now()`. This allows the caller to identify non-report links.
- Add an explicit check to exclude common "form" links like "Submit a collision report" or "Autonomous Vehicle Collision Reports".

### 2. Update `fetch_collision_reports` (`src/av_collisions/fetcher.py`)
- Skip any links that `parse_date_and_company` identifies as invalid or noise.

### 3. Update Bootstrap logic (`src/av_collisions/main.py`)
- Make the `needs_update` logic more aggressive: update if the current date in state is today's date (which is a sign of a parsing failure) and the newly parsed date is different.

## Verification
- Run `uv run av-collisions --bootstrap`.
- Verify that `state.json` no longer contains entries with "Submit" as the company.
- Verify that entries with titles like "Waymo December 29. 2022 (PDF)" now have the correct date "2022-12-29" and company "Waymo".
