# tests/test_seen_posts.py
from src.scrape_reddit import fetch_post
from src.seen_posts import is_seen, mark_seen, DB_PATH
import os

def test_mark_and_check():
    DB_PATH.unlink(missing_ok=True)
    assert not is_seen("test123")
    mark_seen("test123")
    assert is_seen("test123")
    DB_PATH.unlink(missing_ok=True)
