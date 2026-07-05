# Task 5 Report: Video Assembler

**Status:** Complete

**Commit:** 928edab

**Files created:**
- `src/assemble_video.py`

## B-roll shorter-than-audio fix

The brief's `assemble()` applied `.with_duration(duration)` unconditionally, which would let MoviePy try to read frames beyond the clip's natural end. MoviePy's `FFMPEG_VideoReader` does not gracefully handle seeking past the video's duration — it will either error or produce corrupted frames.

**Fix implemented:** A new `_load_broll()` helper checks `bg.duration < duration` and, when the clip is too short, loops it using `concatenate_videoclips([bg] * n_loops, method="chain")` with enough repetitions to cover the full audio duration, then trims with `.with_duration(duration)`. This avoids any out-of-bounds frame reads and produces seamless looping B-roll.
