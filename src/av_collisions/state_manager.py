import json
import os
from typing import Dict, Any

STATE_FILE = "state.json"

def load_state() -> Dict[str, Any]:
    """Loads the state from state.json. Returns an empty dict if the file doesn't exist."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_state(state: Dict[str, Any]) -> None:
    """Saves the state to state.json with indentation for readability."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")

def is_processed(state: Dict[str, Any], url: str) -> bool:
    """Checks if a URL has already been processed."""
    return url in state.get("processed_urls", {})

def mark_processed(state: Dict[str, Any], url: str, metadata: Dict[str, Any]) -> None:
    """Marks a URL as processed and stores associated metadata."""
    if "processed_urls" not in state:
        state["processed_urls"] = {}
    state["processed_urls"][url] = metadata
