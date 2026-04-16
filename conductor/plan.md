# Company Name Cleanup and Force Bootstrap Plan

## Objective
Fix the remaining trailing commas in `state.json` by making the company cleanup logic more robust and forcing an update in the bootstrap mode when the parsed data differs from the existing state.

## Key Files & Context
- `src/av_collisions/fetcher.py`: Contains `clean_company_name`.
- `src/av_collisions/main.py`: Contains the bootstrap update condition.

## Implementation Steps

### 1. Robust Cleanup (`src/av_collisions/fetcher.py`)
- Update `clean_company_name` to use a loop or more comprehensive `rstrip` to remove trailing commas and whitespace repeatedly until none remain.
- Example: `"Ghost Autonomy Inc, "` -> `"Ghost Autonomy Inc"`

### 2. Aggressive Bootstrap Update (`src/av_collisions/main.py`)
- Update the `needs_update` condition in the bootstrap loop.
- Force an update if:
    - `existing_meta.get("company") != report["company"]`
    - `existing_meta.get("date") != report["date"]`
- This ensures that improvements to the parser logic are immediately reflected in `state.json` when running with `--bootstrap`.

### 3. Verification
- Run `uv run av-collisions --bootstrap`.
- Check `state.json` for "Ghost Autonomy Inc" and "Mercedes Benz" (they should no longer have commas).
- Run `ruff` and `mypy`.
