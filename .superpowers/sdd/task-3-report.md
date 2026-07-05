# Task 3: Script Rewriter — Report

**Status:** Complete
**Commit SHA:** 59834c4
**Import verified:** OK — `from src.rewrite_script import rewrite_story` works

## Changes

- **`src/rewrite_script.py`** — Created with `rewrite_story(post: dict) -> str` function wrapping Gemini API (model `gemini-2.5-flash`) with system prompt for Shorts script formatting.
- **`requirements.txt`** — Fixed package name from `google-genai-sdk` (doesn't exist on PyPI) to `google-genai` (the actual package providing `from google import genai`).

## Notes

- `google-genai` 2.10.0 installed successfully; `from google import genai` import verified.
- No tests added (requires live GEMINI_API_KEY).
