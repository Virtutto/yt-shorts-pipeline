import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "seen_posts.db"

def is_seen(post_id: str) -> bool:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS seen (post_id TEXT PRIMARY KEY)")
        cur = conn.execute("SELECT 1 FROM seen WHERE post_id = ?", (post_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()

def mark_seen(post_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS seen (post_id TEXT PRIMARY KEY)")
        conn.execute("INSERT OR IGNORE INTO seen VALUES (?)", (post_id,))
        conn.commit()
    finally:
        conn.close()
