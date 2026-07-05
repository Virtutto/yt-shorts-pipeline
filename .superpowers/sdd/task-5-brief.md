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
