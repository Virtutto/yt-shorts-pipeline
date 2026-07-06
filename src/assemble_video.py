import os
import re
import random
from pathlib import Path
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, ColorClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

VIDEO_W, VIDEO_H = 1080, 1920
CAPTION_SIZE = 56
OUTLINE_WIDTH = 4
MAX_CHUNK_LEN = 22

_FONT_CACHE = {}


def _find_font(size: int) -> ImageFont.FreeTypeFont:
    key = ("font", size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    candidates = [
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            font = ImageFont.truetype(path, size)
            _FONT_CACHE[key] = font
            return font
        except (OSError, IOError):
            continue
    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _group_words(words: list[str]) -> list[list[str]]:
    chunks = []
    i = 0
    while i < len(words):
        if i + 1 < len(words) and len(words[i] + " " + words[i + 1]) <= MAX_CHUNK_LEN:
            chunks.append([words[i], words[i + 1]])
            i += 2
        else:
            chunks.append([words[i]])
            i += 1
    return chunks


def _caption_clip(text: str, cap_w: int, total_h: int, font) -> ImageClip:
    img = Image.new("RGBA", (cap_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (cap_w - tw) // 2
    draw.text((x, OUTLINE_WIDTH), text, font=font, fill="white",
              stroke_width=OUTLINE_WIDTH, stroke_fill=(0, 0, 0, 230))
    return ImageClip(np.array(img))


def _render_timed_captions(word_timings: list[dict], cap_w: int, duration: float) -> list:
    if not word_timings:
        return []
    words = [w["text"] for w in word_timings]
    chunks = _group_words(words)

    font = _find_font(CAPTION_SIZE)
    line_h = CAPTION_SIZE + 10
    pad = OUTLINE_WIDTH
    total_h = line_h + pad * 2

    clips = []
    wi = 0
    for ci, cw in enumerate(chunks):
        start = word_timings[wi]["offset"]
        if ci < len(chunks) - 1:
            next_wi = wi + len(cw)
            end = word_timings[next_wi]["offset"]
        else:
            end = word_timings[-1]["offset"] + word_timings[-1]["duration"]
        chunk_dur = max(end - start, 0.2)

        text = " ".join(cw)
        clip = _caption_clip(text, cap_w, total_h, font).with_duration(chunk_dur).with_start(start)
        clip = clip.with_position(("center", VIDEO_H * 0.82))
        clips.append(clip)
        wi += len(cw)

    return clips


def _render_proportional_captions(sentences: list[str], cap_w: int, duration: float) -> list:
    if not sentences:
        return []

    char_counts = [len(s) for s in sentences]
    total_chars = sum(char_counts)

    font = _find_font(CAPTION_SIZE)
    line_h = CAPTION_SIZE + 10
    pad = OUTLINE_WIDTH
    total_h = line_h + pad * 2

    clips = []
    elapsed = 0.0
    for si, sentence in enumerate(sentences):
        if sentence and sentence[-1] not in ".!?":
            sentence += "."
        words = sentence.split()
        if not words:
            continue
        chunks = _group_words(words)
        sent_dur = (char_counts[si] / total_chars) * duration if total_chars else duration / len(sentences)
        chunk_dur = sent_dur / max(len(chunks), 1)

        for ci, cw in enumerate(chunks):
            text = " ".join(cw)
            clip = _caption_clip(text, cap_w, total_h, font).with_duration(chunk_dur).with_start(elapsed + ci * chunk_dur)
            clip = clip.with_position(("center", VIDEO_H * 0.82))
            clips.append(clip)

        elapsed += sent_dur

    return clips


def _ken_burns(clip: VideoFileClip, target_dur: float | None = None) -> VideoFileClip:
    zoom = random.uniform(1.02, 1.08)
    nw, nh = int(VIDEO_W * zoom), int(VIDEO_H * zoom)
    zoomed = clip.resized((nw, nh))

    margin_x = (nw - VIDEO_W) // 2
    margin_y = (nh - VIDEO_H) // 2
    pan_x = max(int(margin_x * 0.2), 1)
    pan_y = max(int(margin_y * 0.2), 1)
    dx1, dy1 = random.randint(-pan_x, pan_x), random.randint(-pan_y, pan_y)
    dx2, dy2 = random.randint(-pan_x, pan_x), random.randint(-pan_y, pan_y)

    dur = target_dur if target_dur else zoomed.duration

    def pos(t):
        p = t / dur if dur > 0 else 0
        return (dx1 + (dx2 - dx1) * p, dy1 + (dy2 - dy1) * p)

    result = zoomed.with_position(pos)
    if target_dur:
        result = result.with_duration(target_dur)
    return result


def _make_watermark(duration: float) -> ImageClip:
    channel = os.environ.get("CHANNEL_NAME", "Storytime Shorts")
    font = _find_font(28)
    text = f"@{channel}"
    tmp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(tmp)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 8
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), text, font=font, fill=(255, 255, 255, 130))
    return ImageClip(np.array(img), duration=duration).with_position(("right", "bottom")).with_opacity(0.55)


def _load_broll(broll_dir: str, duration: float) -> VideoFileClip | ColorClip:
    paths = sorted(Path(broll_dir).glob("*.mp4"))
    if not paths:
        return ColorClip(size=(VIDEO_W, VIDEO_H), color=(16, 32, 48), duration=duration)

    random.shuffle(paths)
    segments = []
    total = 0.0

    while total < duration:
        for p in paths:
            if total >= duration:
                break
            src = VideoFileClip(str(p))
            need = duration - total
            if src.duration <= need:
                segments.append(_ken_burns(src))
                total += src.duration
            else:
                segments.append(_ken_burns(src, target_dur=need))
                total = duration
        random.shuffle(paths)

    return concatenate_videoclips(segments, method="chain")


def assemble(script: str, audio_path: str, broll_dir: str, output_path: str, word_timings: list[dict] | None = None) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    bg = _load_broll(broll_dir, duration)
    cap_w = VIDEO_W - 80

    if word_timings:
        caption_clips = _render_timed_captions(word_timings, cap_w, duration)
    else:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script) if s.strip()]
        caption_clips = _render_proportional_captions(sentences, cap_w, duration)

    watermark = _make_watermark(duration)
    video = CompositeVideoClip([bg] + caption_clips + [watermark])
    video = video.with_audio(audio)
    video.write_videofile(output_path, codec="libx264", fps=30, preset="fast", audio_codec="aac")
    return output_path
