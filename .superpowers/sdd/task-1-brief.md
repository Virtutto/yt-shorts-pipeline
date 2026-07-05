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
