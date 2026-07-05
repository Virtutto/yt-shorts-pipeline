# Task 2: Reddit Scraper — Report

## What I Created

| File | Status | Notes |
|------|--------|-------|
| `src/seen_posts.py` | Created | `is_seen`, `mark_seen`, `DB_PATH` — added `CREATE TABLE IF NOT EXISTS` to `is_seen` to avoid crash when DB file is empty |
| `src/scrape_reddit.py` | Created | `fetch_post(subreddits)` — exact content from brief |
| `tests/test_seen_posts.py` | Created | Tests `is_seen`/`mark_seen` without network |
| `tests/__init__.py` | Created | Empty package marker |

## Deviation from Brief

- `src/seen_posts.py:is_seen` — added `CREATE TABLE IF NOT EXISTS seen (...)` before the SELECT query. The brief's version omits this, causing `sqlite3.OperationalError: no such table` when `is_seen` is called before `mark_seen` on a fresh DB.

## Test Results

```
$ python -c "from tests.test_seen_posts import *; test_mark_and_check(); print('OK')"
OK
```

## Self-Review Findings

1. **`is_seen` needs table creation** — Fixed as noted above. Without it, calling `is_seen` before `mark_seen` crashes.
2. **`fetch_post` requires env vars at runtime** — `fetch_post` will fail with `KeyError` if `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` are unset. This is expected (runtime credential requirement), but upstream callers must ensure env is configured before calling.
3. **`SUBREDDITS` default** — `os.getenv("REDDIT_SUBREDDITS", "AskReddit+TIFU+ProRevenge+AITAH")` is a module-level constant. Fine for now but could be made a function parameter override; already is via the `subreddits` parameter on `fetch_post`.
4. **DB cleanup** — `seen_posts.db` is in `.gitignore` so it won't be committed. The test cleans up after itself.
5. **Test import of `fetch_post`** — The test imports `fetch_post` but never calls it. If `praw` were missing the import itself would fail, but `praw` is in `requirements.txt` so this is fine.

## Post-Review Fixes Applied (Task 2 Review)

| # | Issue | Severity | File | Fix |
|---|-------|----------|------|-----|
| 1 | SQLite connection leak | Critical | `src/seen_posts.py` | Wrapped `conn` ops in `try/finally` in both `is_seen` and `mark_seen` |
| 2 | Reddit API 50× redundant fetch | Critical | `src/scrape_reddit.py` | Moved `list(sub.hot(limit=50))` outside the loop |
| 3 | Unused import | Important | `tests/test_seen_posts.py` | Removed `from src.scrape_reddit import fetch_post` |
| 4 | `KeyError` on missing env vars | Important | `src/scrape_reddit.py` | Added `_require_env` helper with clear `RuntimeError` message; replaced bare `os.environ[]` access |

## Test Results (Post-Fix)

```
$ python -c "from tests.test_seen_posts import *; test_mark_and_check(); print('OK')"
OK
```
