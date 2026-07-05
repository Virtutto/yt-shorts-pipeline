import os
import random
import re
import requests
from bs4 import BeautifulSoup
from .seen_posts import is_seen, mark_seen

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": USER_AGENT}

SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH").split("+")


def _extract_post_id(thing_id: str) -> str | None:
    m = re.search(r"t3_(\w+)", thing_id)
    return m.group(1) if m else None


def _parse_score(score_el) -> int:
    try:
        return int(score_el.get_text(strip=True))
    except (ValueError, AttributeError):
        return 0


def _scrape_selftext(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
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
        list_url = f"https://old.reddit.com/r/{sub}/hot/"
        try:
            resp = requests.get(list_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        things = soup.select(".thing")

        candidates = []
        for thing in things:
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
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link.startswith("/"):
                link = f"https://old.reddit.com{link}"

            candidates.append({
                "post_id": post_id,
                "title": title,
                "link": link,
                "sub": sub,
                "score": score,
            })

        random.shuffle(candidates)

        for c in candidates:
            selftext = _scrape_selftext(c["link"])
            if selftext or sub.lower() == "askreddit":
                mark_seen(c["post_id"])
                return {
                    "title": c["title"],
                    "selftext": selftext,
                    "subreddit": c["sub"],
                    "permalink": c["link"].replace("old.reddit.com", "www.reddit.com"),
                    "post_id": c["post_id"],
                }

    return None
