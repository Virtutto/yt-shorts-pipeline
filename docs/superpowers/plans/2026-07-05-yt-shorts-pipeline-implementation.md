# YT Shorts Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan.

**Goal:** Fully automated Reddit story → YouTube Shorts pipeline running on GitHub Actions at $0/mo.

**Architecture:** Python pipeline with 5 stages — scrape Reddit (PRAW), rewrite script (Gemini Flash free tier), generate TTS (edge-tts), assemble video (MoviePy + ffmpeg), upload to YouTube (API v3). Cron-triggered via GitHub Actions.

**Tech Stack:** Python 3.11+, PRAW, google-genai-sdk, edge-tts, MoviePy, google-auth-oauthlib, google-auth-httplib2, googleapiclient

## Global Constraints
- All API calls must use free tiers only (Gemini Flash free, YouTube 10K units/day, PRAW, edge-tts)
- Must run entirely in GitHub Actions ubuntu-latest runners
- Videos must be 1080x1920 (9:16), ~60 seconds, H.264
- No hardcoded secrets — all via GitHub Secrets or environment variables
- B-roll assets stored in repo under `assets/broll/`, <50MB total

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `assets/broll/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p yt-shorts-pipeline/{src,.github/workflows,assets/broll,docs/superpowers/specs}
```

- [ ] **Step 2: Write requirements.txt**

```
praw>=7.7,<8
google-genai-sdk>=1.0,<2
edge-tts>=6,<7
moviepy>=2.0,<3
google-auth-oauthlib>=1.0,<2
google-auth-httplib2>=0.1,<1
google-api-python-client>=2.0,<3
Pillow>=10,<11
numpy>=1.24,<2
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
.env
*.db
*.mp3
*.mp4
*.wav
```

- [ ] **Step 4: Write placeholder files**

```bash
touch yt-shorts-pipeline/src/__init__.py
touch yt-shorts-pipeline/assets/broll/.gitkeep
```

- [ ] **Step 5: Install deps and verify**

```bash
cd yt-shorts-pipeline
pip install -r requirements.txt
python -c "import praw; import google_genai; import edge_tts; import moviepy; print('OK')"
```

---

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

### Task 3: Script Rewriter (Gemini API)

**Files:**
- Create: `src/rewrite_script.py`

**Interfaces:**
- Consumes: `fetch_post()` dict
- Produces: `rewrite_story(post: dict) -> str` — returns script text

- [ ] **Step 1: Write rewrite_script.py**

```python
import os
from google import genai

SYSTEM_PROMPT = """You are a YouTube Shorts scriptwriter. Rewrite Reddit stories into 55-65 second scripts.
Rules:
- Start with a hook (first 3 seconds must grab attention)
- Keep natural conversational pacing
- End with a call to action: "What would you do? Comment below."
- Output only the script text, no labels or commentary"""

def rewrite_story(post: dict) -> str:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"Title: {post['title']}\n\nStory:\n{post['selftext']}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[SYSTEM_PROMPT, prompt],
    )
    return response.text.strip()
```

- [ ] **Step 2: Verify import**

```bash
cd yt-shorts-pipeline
python -c "from src.rewrite_script import rewrite_story; print('import OK')"
```

---

### Task 4: TTS Generator (edge-tts)

**Files:**
- Create: `src/generate_audio.py`

**Interfaces:**
- Consumes: script text
- Produces: `generate_tts(script: str, output_path: str) -> list[dict]` — saves audio, returns word timestamps

- [ ] **Step 1: Write generate_audio.py**

```python
import edge_tts
import json

VOICE = "en-US-GuyNeural"

async def generate_tts(script: str, output_path: str) -> list[dict]:
    communicate = edge_tts.Communicate(script, VOICE)
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
    words = []
    async for chunk in communicate.stream():
        if chunk["type"] == "WordBoundary":
            words.append({
                "text": chunk["text"],
                "offset": chunk["offset"] / 1e7,
                "duration": chunk["duration"] / 1e7,
            })
    return words
```

- [ ] **Step 2: Verify import**

```bash
cd yt-shorts-pipeline
python -c "from src.generate_audio import generate_tts; print('import OK')"
```

---

### Task 5: Video Assembler

**Files:**
- Create: `src/assemble_video.py`

**Interfaces:**
- Consumes: script text, audio path, word timestamps, broll path
- Produces: `assemble(script, audio_path, words, broll_dir, output_path)` — exports .mp4

- [ ] **Step 1: Write assemble_video.py** (uses MoviePy 2.x API + Pillow for text rendering)

```python
import random
from pathlib import Path
from moviepy import VideoFileClip, AudioFileClip, ColorClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import textwrap

VIDEO_W, VIDEO_H = 1080, 1920
CAPTION_FONT = "Arial.ttf"
CAPTION_SIZE = 52
MAX_CHARS = 42

def _pick_broll(broll_dir: str) -> str | None:
    clips = list(Path(broll_dir).glob("*.mp4"))
    return str(random.choice(clips)) if clips else None

def _render_caption(text: str, w: int, h: int, duration: float) -> ImageClip:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(CAPTION_FONT, CAPTION_SIZE)
    except OSError:
        font = ImageFont.load_default()
    wrapped = textwrap.fill(text, width=MAX_CHARS)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = h - th - 60
    draw.multiline_text((x + 2, y + 2), wrapped, font=font, fill="black")
    draw.multiline_text((x, y), wrapped, font=font, fill="white")
    return ImageClip(img).with_duration(duration)

def assemble(script: str, audio_path: str, broll_dir: str, output_path: str) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    broll_path = _pick_broll(broll_dir)
    if broll_path:
        bg = VideoFileClip(broll_path).resized((VIDEO_W, VIDEO_H)).with_duration(duration)
    else:
        bg = ColorClip(size=(VIDEO_W, VIDEO_H), color=(16, 32, 48), duration=duration)

    clips = [bg]
    sentences = [s.strip() for s in script.replace("! ", "!\n").replace("? ", "?\n").split(". ") if s.strip()]
    chunk = duration / max(len(sentences), 1)

    for i, sentence in enumerate(sentences):
        cap = _render_caption(sentence + ".", VIDEO_W - 80, 400, chunk)
        cap = cap.with_position(("center", VIDEO_H * 0.7)).with_start(i * chunk)
        clips.append(cap)

    video = CompositeVideoClip(clips)
    video = video.with_audio(audio)
    video.write_videofile(output_path, codec="libx264", fps=30, preset="fast", audio_codec="aac")
    return output_path
```

- [ ] **Step 2: Verify import**

```bash
cd yt-shorts-pipeline
python -c "from src.assemble_video import assemble; print('import OK')"
```

---

### Task 6: YouTube Uploader

**Files:**
- Create: `src/upload_youtube.py`

**Interfaces:**
- Consumes: video file path, post dict
- Produces: `upload(video_path, post)` — uploads to YouTube

- [ ] **Step 1: Write upload_youtube.py**

```python
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "youtube_token.json"

def _get_authenticated_service():
    creds = None
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise RuntimeError("YouTube auth required — run auth setup locally first")
    return build("youtube", "v3", credentials=creds)

def upload(video_path: str, post: dict) -> str:
    youtube = _get_authenticated_service()
    body = {
        "snippet": {
            "title": f"{post['title']} #shorts",
            "description": f"Story from r/{post['subreddit']}\n\n{post['permalink']}",
            "tags": ["shorts", "reddit", "storytime", post["subreddit"]],
        },
        "status": {"privacyStatus": "public"},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return f"https://youtu.be/{response['id']}"
```

- [ ] **Step 2: Verify import**

```bash
cd yt-shorts-pipeline
python -c "from src.upload_youtube import upload; print('import OK')"
```

---

### Task 7: Main Pipeline + GitHub Actions

**Files:**
- Create: `src/main.py`
- Create: `.github/workflows/daily-shorts.yml`

- [ ] **Step 1: Write main.py**

```python
import os
import sys
import tempfile
from pathlib import Path
from src.scrape_reddit import fetch_post
from src.rewrite_script import rewrite_story
from src.generate_audio import generate_tts
from src.assemble_video import assemble
from src.upload_youtube import upload
import asyncio

BROLL_DIR = str(Path(__file__).parent.parent / "assets" / "broll")

async def main():
    print("[1/5] Scraping Reddit...")
    post = fetch_post()
    if not post:
        print("No suitable post found")
        return

    print(f"[2/5] Rewriting script for: {post['title']}")
    script = rewrite_story(post)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = f"{tmp}/audio.mp3"
        print("[3/5] Generating TTS...")
        words = await generate_tts(script, audio_path)

        video_path = f"{tmp}/output.mp4"
        print("[4/5] Assembling video...")
        assemble(script, audio_path, BROLL_DIR, video_path)

        print("[5/5] Uploading to YouTube...")
        url = upload(video_path, post)
        print(f"DONE: {url}")

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Write daily-shorts.yml**

```yaml
name: Daily Shorts

on:
  schedule:
    - cron: '0 10,18 * * *'
  workflow_dispatch:

jobs:
  create-short:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pipeline
        run: python -m src.main
        env:
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          YOUTUBE_TOKEN_JSON: ${{ secrets.YOUTUBE_TOKEN_JSON }}

      - name: Upload video artifact
        uses: actions/upload-artifact@v4
        with:
          name: short-video
          path: /tmp/output.mp4
```

---

### Task 8: YouTube Auth Setup Script

**Files:**
- Create: `src/auth_youtube.py`

- [ ] **Step 1: Write auth_youtube.py**

```python
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secrets.json"  # Download from Google Cloud Console

def run_local_auth():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    print("Add this JSON to your GitHub secret YOUTUBE_TOKEN_JSON:")
    print(json.dumps(json.loads(creds.to_json()), indent=2))

if __name__ == "__main__":
    run_local_auth()
```

- [ ] **Step 2: Add setup instructions to README**

```markdown
# Setup

1. **Reddit API**: Go to https://www.reddit.com/prefs/apps → create app → get client_id + client_secret
2. **Gemini API**: Go to https://aistudio.google.com → create API key (free tier)
3. **YouTube API**: Go to Google Cloud Console → enable YouTube Data API v3 → create OAuth 2.0 credentials (Desktop) → download client_secrets.json → run `python src/auth_youtube.py` → copy refresh token JSON
4. **Add GitHub Secrets**: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, GEMINI_API_KEY, YOUTUBE_TOKEN_JSON
5. **Push to GitHub**: The workflow will run at 10:00 and 18:00 UTC daily
```

- [ ] **Step 3: Verify full pipeline dry-run locally**

```bash
cd yt-shorts-pipeline
# Export required env vars, then:
python -c "from src.main import main; import asyncio; asyncio.run(main())"
```
