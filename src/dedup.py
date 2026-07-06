import re
import json
from pathlib import Path

HASHES_PATH = Path(__file__).parent.parent / "data" / "story_hashes.json"

SIMILARITY_THRESHOLD = 0.45

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "was", "were", "are", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "not", "no", "nor",
    "so", "very", "just", "then", "now", "here", "there",
    "get", "got", "go", "went", "come", "came", "make", "made",
    "like", "know", "think", "see", "want", "say", "said", "tell",
    "back", "even", "still", "also", "well", "really", "actually",
}


def _normalize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _load() -> list[dict]:
    if not HASHES_PATH.exists():
        return []
    try:
        data = json.load(open(HASHES_PATH))
        if data and isinstance(data[0], str):
            _save([])
            return []
        return data
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]):
    HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HASHES_PATH, "w") as f:
        json.dump(entries, f)


def is_seen(text: str) -> bool:
    words = _normalize(text)
    if not words:
        return False
    for entry in _load():
        if isinstance(entry, str):
            continue
        existing = set(entry["words"].split(" "))
        if _jaccard(words, existing) >= SIMILARITY_THRESHOLD:
            return True
    return False


def mark_seen(text: str):
    words = sorted(_normalize(text))
    if not words:
        return
    entries = _load()
    entry = {"words": " ".join(words)}
    if entry not in entries:
        entries.append(entry)
        _save(entries)
