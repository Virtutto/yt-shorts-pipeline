### Task 2: Reddit Scraper

**Files:**
- Create: `src/scrape_reddit.py`
- Create: `src/seen_posts.py`

**Interfaces:**
- Produces: `fetch_post(subreddits: list[str]) -> dict` — returns `{title, selftext, subreddit, permalink, post_id}`

- [ ] **Step 1: Write seen_posts.py**

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "seen_posts.db"

def is_seen(post_id: str) -> bool:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute("SELECT 1 FROM seen WHERE post_id = ?", (post_id,))
    seen = cur.fetchone() is not None
    conn.close()
    return seen

def mark_seen(post_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("CREATE TABLE IF NOT EXISTS seen (post_id TEXT PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO seen VALUES (?)", (post_id,))
    conn.commit()
    conn.close()
```

- [ ] **Step 2: Write scrape_reddit.py**

```python
import os
import random
import praw
from .seen_posts import is_seen, mark_seen

SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH")

def fetch_post(subreddits: str = SUBREDDITS) -> dict | None:
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent="yt-shorts-pipeline/1.0",
    )
    sub = reddit.subreddit(subreddits)
    for _ in range(50):
        post = random.choice(list(sub.hot(limit=50)))
        if not is_seen(post.id) and post.score >= 100 and post.selftext:
            mark_seen(post.id)
            return {
                "title": post.title,
                "selftext": post.selftext[:2000],
                "subreddit": post.subreddit.display_name,
                "permalink": post.permalink,
                "post_id": post.id,
            }
    return None
```

- [ ] **Step 3: Write test**

```python
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
```

```bash
cd yt-shorts-pipeline
python -c "from tests.test_seen_posts import *; test_mark_and_check(); print('OK')"
```

---
