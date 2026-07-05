import sys
from pathlib import Path
from moviepy import VideoFileClip

src = sys.argv[1]
duration = VideoFileClip(src).duration
segments = int(sys.argv[2]) if len(sys.argv) > 2 else 5
out_dir = Path("assets/broll")
out_dir.mkdir(parents=True, exist_ok=True)

for i in range(segments):
    start = duration / segments * i
    end = start + min(15, duration / segments)
    clip = VideoFileClip(src).subclipped(start, end)
    path = out_dir / f"broll_{i+1}.mp4"
    clip.write_videofile(str(path), codec="libx264", audio_codec="aac")
    print(f"Created {path}")
print("Done!")
