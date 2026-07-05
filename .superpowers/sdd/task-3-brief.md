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
