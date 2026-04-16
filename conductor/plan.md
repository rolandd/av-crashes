# Autonomous Mode Boolean Normalization Plan

## Objective
Normalize the `autonomous_mode` metadata from raw PDF export strings (like `"/Autonomous"` or `"/Off"`) to standard boolean values (`true`/`false`). This makes the code and `state.json` cleaner and more intuitive.

## Key Files & Context
- `src/av_collisions/pdf_parser.py`: Where the checkbox values are extracted.
- `src/av_collisions/bluesky.py`: Where the status text for posts is generated.
- `src/av_collisions/main.py`: Where the value is returned and stored in state.

## Implementation Steps

### 1. Refactor `src/av_collisions/pdf_parser.py`
- In `extract_section_5`, initialize `autonomous_mode` and `conventional_mode` to `False`.
- Update the widget loop: set the value to `True` if `field_value` is present and not `"/Off"`.

### 2. Refactor `src/av_collisions/bluesky.py`
- Simplify the status check: `status = "yes" if metadata.get("autonomous_mode") else "no"`.

### 3. Refactor `src/av_collisions/main.py`
- Update the return type hint of `process_single_report` from `str | None` to `bool | None`.
- The logic inside `process_single_report` and the main loop will naturally handle the boolean value.

## Verification
- Run `uv run ruff check` and `uv run mypy`.
- Run a local test with `--url` to ensure the metadata JSON reflects the boolean change.
