import hashlib
import json
from pathlib import Path

HASHES_PATH = Path(__file__).parent.parent / "data" / "story_hashes.json"


def _load_hashes() -> list:
    if not HASHES_PATH.exists():
        return []
    try:
        with open(HASHES_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_hashes(hashes: list):
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASHES_PATH, "w") as f:
        json.dump(hashes, f)


def story_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def is_seen(text: str) -> bool:
    return story_hash(text) in _load_hashes()


def mark_seen(text: str):
    h = story_hash(text)
    hashes = _load_hashes()
    if h not in hashes:
        hashes.append(h)
        _save_hashes(hashes)
