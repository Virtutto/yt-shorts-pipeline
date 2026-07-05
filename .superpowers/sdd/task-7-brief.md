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
