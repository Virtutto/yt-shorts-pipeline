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
