import os
import random
from pathlib import Path
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, ColorClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap

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


def _render_caption(text: str, w: int, duration: float) -> ImageClip:
    font = _find_font(CAPTION_SIZE)
    wrapped = textwrap.fill(text, width=MAX_CHARS)
    lines_list = wrapped.split("\n")
    line_h = CAPTION_SIZE + 10
    pad = OUTLINE_WIDTH
    total_h = len(lines_list) * line_h + pad * 2

    img = Image.new("RGBA", (w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines_list):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = pad + i * line_h

        draw.text((x, y), line, font=font, fill="white",
                  stroke_width=OUTLINE_WIDTH, stroke_fill=(0, 0, 0, 230))

    return ImageClip(np.array(img)).with_duration(duration)


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
        cap = _render_caption(sentence + ".", cap_w, chunk)
        cap = cap.with_position(("center", VIDEO_H * 0.82)).with_start(i * chunk)
        clips.append(cap)

    video = CompositeVideoClip(clips)
    video = video.with_audio(audio)
    video.write_videofile(output_path, codec="libx264", fps=30, preset="fast", audio_codec="aac")
    return output_path
