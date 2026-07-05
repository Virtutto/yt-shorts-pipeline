import os
import random
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from .seen_posts import is_seen, mark_seen

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH").split("+")


def _extract_post_id(entry_id: str) -> str | None:
    m = re.search(r"/comments/(\w+)/", entry_id)
    return m.group(1) if m else None


def _scrape_selftext(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        div = soup.select_one(".usertext-body .md")
        if div:
            text = div.get_text(strip=True)
            return text[:2000]
        return ""
    except Exception:
        return ""


def fetch_post(subreddits: list[str] | None = None) -> dict | None:
    subs = subreddits or SUBREDDITS
    random.shuffle(subs)

    for sub in subs:
        rss_url = f"https://www.reddit.com/r/{sub}/hot/.rss"
        try:
            feed = feedparser.parse(rss_url, agent=USER_AGENT)
        except Exception:
            continue

        entries = list(feed.entries)
        random.shuffle(entries)

        for entry in entries:
            post_id = _extract_post_id(entry.id)
            if not post_id or is_seen(post_id):
                continue

            title = entry.title
            link = f"https://old.reddit.com{entry.link}" if entry.link.startswith("/r/") else entry.link
            selftext = _scrape_selftext(link)

            if selftext or sub.lower() == "askreddit":
                mark_seen(post_id)
                return {
                    "title": title,
                    "selftext": selftext,
                    "subreddit": sub,
                    "permalink": f"https://reddit.com{entry.link}" if entry.link.startswith("/r/") else entry.link,
                    "post_id": post_id,
                }

    return None
