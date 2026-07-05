import os
import random
import praw
from .seen_posts import is_seen, mark_seen

SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def fetch_post(subreddits: str = SUBREDDITS) -> dict | None:
    reddit = praw.Reddit(
        client_id=_require_env("REDDIT_CLIENT_ID"),
        client_secret=_require_env("REDDIT_CLIENT_SECRET"),
        user_agent="yt-shorts-pipeline/1.0",
    )
    sub = reddit.subreddit(subreddits)
    posts = list(sub.hot(limit=50))
    for _ in range(50):
        if not posts:
            break
        post = random.choice(posts)
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
