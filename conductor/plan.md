# Type Annotations and Linting Tooling Plan

## Objective
Enhance project maintainability by fully typing the Python codebase and adding `ruff` (for linting and formatting) and `mypy` (for strict static type checking) as development dependencies. 

## Key Files & Context
- `pyproject.toml`: To add `ruff` and `mypy` as dev dependencies.
- `src/av_collisions/main.py`: Missing `-> None` on `main()`, etc.
- `src/av_collisions/fetcher.py`: Has types but can be refined.
- `src/av_collisions/bluesky.py`: Missing return types (e.g. `-> None`).
- `src/av_collisions/pdf_parser.py`: Existing types can be audited.
- `src/av_collisions/state_manager.py`: Mostly typed, audit for completeness.

## Implementation Steps

### 1. Update Dependencies
- Modify `pyproject.toml` to add `ruff` and `mypy` to the `[dependency-groups] dev` list.
- Run `uv sync` or let the environment pick up the changes if using `uv run`.

### 2. Add Type Annotations
- Audit all functions in `src/av_collisions/` and ensure they have full type signatures for arguments and return values (e.g. adding `-> None` to functions that do not return).
- Import `typing` modules where necessary (`List`, `Dict`, `Any`, `Optional`, `Tuple`).

### 3. Run Formatters and Linters
- Execute `uv run ruff format src/av_collisions/` to ensure a consistent code style.
- Execute `uv run ruff check --fix src/av_collisions/` to automatically fix any basic linting errors.
- Execute `uv run mypy src/av_collisions/` to enforce strict static typing and resolve any issues that arise.

## Verification & Testing
- Ensure that `uv run ruff check` and `uv run mypy` both exit with status code `0` after the changes are applied.
- Ensure the scraper can still run without runtime type errors.
