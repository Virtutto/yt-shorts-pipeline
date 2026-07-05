# Setup

1. **Reddit API**: Go to https://www.reddit.com/prefs/apps → create app → get client_id + client_secret
2. **Gemini API**: Go to https://aistudio.google.com → create API key (free tier)
3. **YouTube API**: Go to Google Cloud Console → enable YouTube Data API v3 → create OAuth 2.0 credentials (Desktop) → download client_secrets.json → run `python src/auth_youtube.py` → copy refresh token JSON
4. **Add GitHub Secrets**: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, GEMINI_API_KEY, YOUTUBE_TOKEN_JSON
5. **Push to GitHub**: The workflow will run at 10:00 and 18:00 UTC daily
