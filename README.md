# Setup

1. **Groq API**: Go to https://console.groq.com → sign up → go to https://console.groq.com/keys → create API key
2. **YouTube API**: Go to Google Cloud Console → enable YouTube Data API v3 → create OAuth 2.0 credentials (Desktop) → download client_secrets.json → run `python src/auth_youtube.py` → copy refresh token JSON
3. **Add GitHub Secrets**: GROQ_API_KEY, YOUTUBE_TOKEN_JSON
4. **Push to GitHub**: The workflow will run at 10:00 and 18:00 UTC daily
5. **Add B-roll clips**: Drop Minecraft parkour `.mp4` files into `assets/broll/` (5-10 clips, 10+ sec each)
