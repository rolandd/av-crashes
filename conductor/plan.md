# Bluesky Refactoring Plan

## Objective
Update the `post_to_bluesky` function and its caller to accept and pass image data directly as bytes, eliminating the need to write temporary files to disk before uploading to Bluesky.

## Key Files & Context
- `src/av_collisions/bluesky.py`: The `post_to_bluesky` function currently takes an `image_path` string and reads the file.
- `src/av_collisions/main.py`: The `process_single_report` function currently writes the `image_bytes` to a temporary file before calling `post_to_bluesky`.

## Implementation Steps

### 1. Refactor `src/av_collisions/bluesky.py`
- Modify the signature of `post_to_bluesky`. Change `image_path: str` to `image_bytes: bytes`.
- Remove the `with open(image_path, "rb") as f:` block.
- Update the `client.upload_blob` call to use the passed `image_bytes` directly instead of `img_data`.

### 2. Refactor `src/av_collisions/main.py`
- Remove the `import tempfile` line and the `import os` if it becomes completely unused (though it's still used for `os.makedirs` in `pdf_parser` and `os.path.exists` isn't needed here anymore, but `os` might still be used for other things. Wait, `main.py` uses `os.makedirs`? No, `main.py` uses `os.environ`? No, `main.py` uses `os.makedirs` at the top? Wait, the latest `main.py` doesn't have `os.makedirs("data/images")` anymore. Let's just remove `tempfile` and the specific `os` calls for tmp paths).
- In `process_single_report`, remove the `with tempfile.NamedTemporaryFile(...) as tmp:` block.
- Update the `post_to_bluesky` call to directly pass `image_bytes` instead of the temporary file path.
- Remove the `try...finally` block that cleans up the temporary file.

## Verification
- Run `uv run ruff check src/av_collisions` and `uv run mypy src/av_collisions` to ensure the type signatures are correct and there are no linting errors.
- (Optional) Test locally with `--url` to ensure it still works, although `--url` doesn't post to Bluesky anyway.