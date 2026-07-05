# AI YouTube Shorts Pipeline

Fully automated pipeline: Reddit stories → AI-rewritten scripts → TTS voiceover → video assembly → YouTube upload. Runs entirely on GitHub Actions at $0/month.

## Architecture

```
[Reddit API] → [Python Scraper] → [Gemini API] → [edge-tts] → [ffmpeg/MoviePy] → [YouTube API]
                PRAW (free)         Flash free tier    (free)         (free)          Free quota
```

## Components

### 1. Content Scraper (`scrape_reddit.py`)
- Uses PRAW (Python Reddit API Wrapper) — free, requires Reddit app registration
- Polls configured subreddits: r/AskReddit, r/TIFU, r/ProRevenge, r/AITAH
- Filters: min score 100, excludes previously-used posts (SQLite seen-posts DB)
- Returns: post title, selftext, subreddit, permalink

### 2. Script Rewriter (`rewrite_script.py`)
- Calls Gemini 2.5 Flash free tier API (15 RPM free, ~1,500 requests/day)
- Prompt: Rewrite Reddit story into 55-65 second YouTube Shorts script:
  - Hook (first 3 seconds)
  - Story body with natural pacing
  - Call to action (like/subscribe)
- Returns: plain text script with word-level timestamps from TTS

### 3. TTS Generator (`generate_audio.py`)
- Uses edge-tts (free, no API key, Microsoft Edge TTS servers)
- Voice: `en-US-GuyNeural` (US male, natural)
- Returns: MP3 audio file + word-level timing data for captions

### 4. Video Assembler (`assemble_video.py`)
- Uses MoviePy + ffmpeg (pre-installed on GitHub runners)
- Takes: B-roll clip (random from asset library), TTS audio, captions
- Adds: burned-in captions (white text, black stroke, centered bottom), Ken Burns zoom on B-roll
- Exports: 1080x1920 (9:16), ~60 seconds, H.264, ~30fps
- B-roll: ~20 Minecraft parkour clips (free-use from Pixabay), ~50MB total in repo

### 5. YouTube Uploader (`upload_youtube.py`)
- YouTube Data API v3 — free quota: 10,000 units/day
- videos.insert costs ~100 units per upload (updated Dec 2025)
- ~100 uploads/day possible on free tier; we need 1-2
- Video metadata: title = Reddit post title + "#shorts", description = story credit + links
- Publishes immediately or schedules via publishAt parameter

### 6. GitHub Actions Workflow (`.github/workflows/daily-shorts.yml`)
- Schedule: cron `0 10,18 * * *` (twice daily UTC)
- Runs on: ubuntu-latest
- Steps: checkout → setup Python → install deps → run pipeline → upload artifact
- Secrets: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, GEMINI_API_KEY, YOUTUBE_CREDENTIALS

## Free Tier Limits Confirmed

| Service | Limit | Our usage | Headroom |
|---------|-------|-----------|----------|
| Gemini 2.5 Flash | 15 RPM, 1,500 RPD | 2 calls/day | 750x |
| YouTube Data API | 10,000 units/day | ~200 units/day (2 uploads) | 50x |
| GitHub Actions | 2,000 min/month | ~30 min/month (10 min/run × 60 runs) | 65x |
| edge-tts | Unlimited (Microsoft endpoint) | 2 calls/day | effectively unlimited |
| PRAW | Unlimited (Reddit API) | 2 calls/day | effectively unlimited |

## Channel Setup (one-time, ~15 minutes)
1. Create Google account for YouTube channel
2. Create Google Cloud project → enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app type)
4. Run auth script once locally to get refresh token → store as GitHub secret
5. Get Gemini API key from Google AI Studio (free tier)
6. Register Reddit app → get client_id + client_secret

## File Structure

```
yt-shorts-pipeline/
├── .github/workflows/daily-shorts.yml
├── src/
│   ├── scrape_reddit.py
│   ├── rewrite_script.py
│   ├── generate_audio.py
│   ├── assemble_video.py
│   └── upload_youtube.py
├── assets/broll/           # Minecraft parkour clips (free-use)
├── seen_posts.db           # SQLite, prevents repeat content
├── requirements.txt
└── README.md
```

## Estimated Costs
- $0/month (all services on free tiers)
- The only potential cost is if Gemini free tier limits are exceeded (unlikely at 2 calls/day)
