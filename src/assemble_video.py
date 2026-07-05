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


def _render_karaoke_words(sentence: str, cap_w: int, total_duration: float) -> list:
    font = _find_font(CAPTION_SIZE)
    wrapped = textwrap.fill(sentence, width=MAX_CHARS)
    lines = wrapped.split("\n")

    word_map = []
    for li, line in enumerate(lines):
        for w in line.split(" "):
            word_map.append((li, w))

    n_words = len(word_map)
    if n_words == 0:
        return []

    word_duration = total_duration / n_words
    line_h = CAPTION_SIZE + 10
    pad = OUTLINE_WIDTH
    total_h = len(lines) * line_h + 60

    space_w = None
    clips = []

    for highlight_idx in range(n_words):
        img = Image.new("RGBA", (cap_w, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        widx = 0
        x = 0
        for line_idx, line in enumerate(lines):
            line_bbox = draw.textbbox((0, 0), line, font=font)
            line_w = line_bbox[2] - line_bbox[0]
            x_offset = (cap_w - line_w) // 2

            for word in line.split(" "):
                w_bbox = draw.textbbox((0, 0), word, font=font)
                w_w = w_bbox[2] - w_bbox[0]

                if space_w is None:
                    space_bbox = draw.textbbox((0, 0), " ", font=font)
                    space_w = space_bbox[2] - space_bbox[0]

                y = pad + line_idx * line_h
                is_hl = widx == highlight_idx
                color = "white" if is_hl else (160, 160, 160)

                draw.text((x_offset + x, y), word, font=font, fill=color,
                          stroke_width=OUTLINE_WIDTH, stroke_fill=(0, 0, 0, 200))

                x += w_w + space_w
                widx += 1

            x = 0

        clip = ImageClip(np.array(img)).with_duration(word_duration)
        clip = clip.with_position(("center", VIDEO_H * 0.82)).with_start(highlight_idx * word_duration)
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
        word_clips = _render_karaoke_words(sentence + ".", cap_w, chunk)
        sent_start = i * chunk
        for wc in word_clips:
            clips.append(wc.with_start(wc.start + sent_start))

    video = CompositeVideoClip(clips)
    video = video.with_audio(audio)
    video.write_videofile(output_path, codec="libx264", fps=30, preset="fast", audio_codec="aac")
    return output_path
