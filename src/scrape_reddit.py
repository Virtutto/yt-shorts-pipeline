import os
import random
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from .seen_posts import is_seen, mark_seen
from .dedup import is_seen as is_dup_text

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH").split("+")


def _extract_post_id(text: str) -> str | None:
    m = re.search(r"t3_(\w+)", text)
    if m:
        return m.group(1)
    m = re.search(r"/comments/(\w+)/", text)
    return m.group(1) if m else None


def _parse_score(score_el) -> int:
    try:
        return int(score_el.get_text(strip=True))
    except (ValueError, AttributeError):
        return 0


def _try_rss(sub: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/hot/.rss"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  RSS {sub}: HTTP {resp.status_code}")
            return []
        feed = feedparser.parse(resp.text)
        results = []
        for entry in feed.entries:
            post_id = _extract_post_id(entry.get("id", ""))
            if not post_id or is_seen(post_id):
                continue
            title = entry.get("title", "")
            link = entry.get("link", "")
            results.append({
                "post_id": post_id,
                "title": title,
                "link": link.replace("https://www.reddit.com", "https://old.reddit.com"),
                "sub": sub,
            })
        return results
    except Exception as e:
        print(f"  RSS {sub}: {e}")
        return []


def _try_old_reddit(sub: str) -> list[dict]:
    url = f"https://old.reddit.com/r/{sub}/hot/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  old.reddit {sub}: HTTP {resp.status_code}")
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        candidates = []
        for thing in soup.select(".thing"):
            post_id = _extract_post_id(thing.get("id", ""))
            if not post_id or is_seen(post_id):
                continue
            score_el = thing.select_one(".score.unvoted")
            score = _parse_score(score_el) if score_el else 0
            if score < 100:
                continue
            title_el = thing.select_one("a.title")
            if not title_el:
                continue
            link = title_el.get("href", "")
            if link.startswith("/"):
                link = f"https://old.reddit.com{link}"
            candidates.append({
                "post_id": post_id,
                "title": title_el.get_text(strip=True),
                "link": link,
                "sub": sub,
            })
        return candidates
    except Exception as e:
        print(f"  old.reddit {sub}: {e}")
        return []


def _scrape_selftext(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        div = soup.select_one(".usertext-body .md")
        if div:
            return div.get_text(strip=True)[:2000]
        return ""
    except Exception:
        return ""


def fetch_post(subreddits: list[str] | None = None) -> dict | None:
    subs = subreddits or SUBREDDITS
    random.shuffle(subs)

    for sub in subs:
        print(f"  Trying r/{sub}...")
        candidates = _try_rss(sub)
        if not candidates:
            candidates = _try_old_reddit(sub)
        if not candidates:
            print(f"  No candidates from r/{sub}")
            continue

        random.shuffle(candidates)

        for c in candidates:
            selftext = _scrape_selftext(c["link"])
            if selftext or sub.lower() == "askreddit":
                if selftext and is_dup_text(selftext):
                    print(f"  Story text is a near-duplicate, skipping")
                    continue
                mark_seen(c["post_id"])
                return {
                    "title": c["title"],
                    "selftext": selftext,
                    "subreddit": c["sub"],
                    "permalink": c["link"].replace("old.reddit.com", "www.reddit.com"),
                    "post_id": c["post_id"],
                }

    return None
