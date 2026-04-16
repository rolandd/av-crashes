# State Schema Simplification Plan

## Objective
Reduce the size and redundancy of `state.json` by removing fields that are either duplicate (like `url`, which is already the key) or no longer necessary (like `slug`, which was for persistent storage).

## Key Files & Context
- `src/av_collisions/main.py`: Where the state metadata is constructed.
- `state.json`: The data file to be migrated.

## Implementation Steps

### 1. Update `src/av_collisions/main.py`
- Modify the `metadata` dictionary in the `bootstrap` block to only include: `raw_title`, `company`, `date`, `processed_at`, and `bootstrapped`.
- Modify the `metadata` dictionary in the normal processing loop to only include: `raw_title`, `company`, `date`, and `processed_at`.
- (The `slug` is still used for local testing and filename generation, so the `slugify` logic remains, but it won't be stored in the state).

### 2. Migrate `state.json`
- Create and run a temporary Python script to strip the redundant fields from all entries in `processed_urls`.

### 3. Verification
- Run `uv run ruff check` and `uv run mypy`.
- Run `uv run av-collisions --bootstrap` to ensure state is still recognized correctly.
- Inspect `state.json` to confirm the leaner format.
