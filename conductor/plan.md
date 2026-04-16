# Data Schema Refactor Plan

## Objective
Update the internal metadata schema to use more accurate and standard field names:
1. Rename `date_text` to `raw_title`.
2. Rename `filename_base` to `slug`.

This involves updating the source code and migrating the existing `state.json` file.

## Key Files & Context
- `src/av_collisions/fetcher.py`: Where `date_text` is first parsed.
- `src/av_collisions/main.py`: Where the metadata is constructed and passed.
- `src/av_collisions/pdf_parser.py`: Where `filename_base` is used to generate filenames.
- `state.json`: The historical record that needs to be migrated.

## Implementation Steps

### 1. Refactor `src/av_collisions/fetcher.py`
- Update `fetch_collision_reports()` to use the key `raw_title` instead of `date_text` in its returned list of dicts.

### 2. Refactor `src/av_collisions/pdf_parser.py`
- Update `save_output()` function signature: rename `filename_base: str` to `slug: str`.
- Update the internal logic to use `slug` to generate `.png` and `.json` filenames.

### 3. Refactor `src/av_collisions/main.py`
- Update all instances of `date_text` to `raw_title`.
- Update all instances of `filename_base` to `slug`.
- Ensure `process_single_report` and the `main()` loop pass and store the new keys.

### 4. Migrate `state.json`
- Use a `sed` command or a temporary Python script to rename the keys in `state.json` for all processed entries.
- Command for `sed`: `sed -i 's/"date_text":/"raw_title":/g' state.json` and `sed -i 's/"filename_base":/"slug":/g' state.json`.

## Verification
- Run `uv run ruff check src/av_collisions` and `uv run mypy src/av_collisions` to ensure all type signatures and calls are correct.
- Perform a manual check of `state.json` to verify the keys have been renamed.
- Run the scraper with `--bootstrap` (it should identify that URLs are already processed because `is_processed` only checks for URL presence in the top-level keys, but the values inside should be updated).
