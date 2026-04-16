# Autonomous Mode Persistence Plan

## Objective
Update `state.json` to include the `autonomous_mode` status (extracted from Section 5 of the PDF) for all newly processed reports. This ensures that the state file provides a more complete picture of each report without needing to re-parse the PDF.

## Key Files & Context
- `src/av_collisions/main.py`: The `process_single_report` function extracts `extra_metadata` from the PDF, which contains the `autonomous_mode` field.
- `state.json`: The format of processed entries will be updated.

## Implementation Steps

### 1. Update `src/av_collisions/main.py`
- In the normal processing loop (inside `main()`), ensure the `metadata` dictionary saved to `state` includes the `autonomous_mode` value.
- Update `process_single_report` to return the `autonomous_mode` value so it can be easily added to the state in the main loop.

### 2. Verification
- Run `uv run av-collisions --url <PDF_URL>` (Local test mode doesn't update state, but ensures code still runs).
- (Optional) Run a normal scrape or simulate a new report to verify `state.json` now includes `autonomous_mode`.
- Run `ruff` and `mypy` checks.
