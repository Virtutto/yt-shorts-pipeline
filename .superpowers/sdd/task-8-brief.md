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
