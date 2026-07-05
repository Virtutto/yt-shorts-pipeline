# Task 7 Report: Main Pipeline + GitHub Actions Workflow

**Status:** Complete

**Commit SHA:** `3397e39`

## Files Created

| File | Description |
|------|-------------|
| `src/main.py` | Orchestrates the 5-step pipeline: scrape Reddit → rewrite script → generate TTS → assemble video → upload to YouTube |
| `.github/workflows/daily-shorts.yml` | Scheduled workflow runs at 10:00 and 18:00 UTC daily, with manual dispatch support |

## Bugs Fixed from Brief

Two issues in the original brief were corrected:

1. **Removed unused `words` variable** — the brief had `words = await generate_tts(script, audio_path)` but `assemble()` doesn't accept a `words` parameter (its signature is `assemble(script, audio_path, broll_dir, output_path)`). Fixed by calling `await generate_tts(script, audio_path)` without capturing the return value.

2. **Removed artifact upload step** — the brief's workflow included an `actions/upload-artifact@v4` step referencing `/tmp/output.mp4`, but the video file is created inside a `TemporaryDirectory` context manager that deletes the directory on exit. Since the video is already uploaded to YouTube, the artifact step is unnecessary.
