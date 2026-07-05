import os
import random
from pathlib import Path
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, ColorClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

VIDEO_W, VIDEO_H = 1080, 1920
CAPTION_SIZE = 56
MAX_CHARS = 38
OUTLINE_WIDTH = 4

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


MAX_CHUNK_LEN = 22


def _render_word_chunks(sentence: str, cap_w: int, total_duration: float) -> list:
    words = sentence.split()
    if not words:
        return []

    chunks = []
    i = 0
    while i < len(words):
        if i + 1 < len(words) and len(words[i] + " " + words[i + 1]) <= MAX_CHUNK_LEN:
            chunks.append(words[i] + " " + words[i + 1])
            i += 2
        else:
            chunks.append(words[i])
            i += 1

    chunk_dur = total_duration / max(len(chunks), 1)

    font = _find_font(CAPTION_SIZE)
    line_h = CAPTION_SIZE + 10
    pad = OUTLINE_WIDTH
    total_h = line_h + pad * 2

    clips = []
    for idx, chunk in enumerate(chunks):
        img = Image.new("RGBA", (cap_w, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bbox = draw.textbbox((0, 0), chunk, font=font)
        tw = bbox[2] - bbox[0]
        x = (cap_w - tw) // 2
        y = pad

        draw.text((x, y), chunk, font=font, fill="white",
                  stroke_width=OUTLINE_WIDTH, stroke_fill=(0, 0, 0, 230))

        clip = ImageClip(np.array(img)).with_duration(chunk_dur)
        clip = clip.with_position(("center", VIDEO_H * 0.82)).with_start(idx * chunk_dur)
        clips.append(clip)

    return clips


def _load_broll(broll_dir: str, duration: float) -> VideoFileClip | ColorClip:
    broll_path = _pick_broll(broll_dir)
    if not broll_path:
        return ColorClip(size=(VIDEO_W, VIDEO_H), color=(16, 32, 48), duration=duration)
    bg = VideoFileClip(broll_path).resized((VIDEO_W, VIDEO_H))
    if bg.duration < duration:
        n_loops = int(duration // bg.duration) + 1
        bg = concatenate_videoclips([bg.copy() for _ in range(n_loops)], method="chain").with_duration(duration)
    else:
        bg = bg.with_duration(duration)
    return bg


def _pick_broll(broll_dir: str) -> str | None:
    clips = list(Path(broll_dir).glob("*.mp4"))
    return str(random.choice(clips)) if clips else None


def assemble(script: str, audio_path: str, broll_dir: str, output_path: str) -> str:
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    bg = _load_broll(broll_dir, duration)

    clips = [bg]
    sentences = [s.strip() for s in script.replace("! ", "!\n").replace("? ", "?\n").split(". ") if s.strip()]
    chunk = duration / max(len(sentences), 1)

    cap_w = VIDEO_W - 80

    for i, sentence in enumerate(sentences):
        word_clips = _render_word_chunks(sentence + ".", cap_w, chunk)
        sent_start = i * chunk
        for wc in word_clips:
            clips.append(wc.with_start(wc.start + sent_start))

    video = CompositeVideoClip(clips)
    video = video.with_audio(audio)
    video.write_videofile(output_path, codec="libx264", fps=30, preset="fast", audio_codec="aac")
    return output_path
