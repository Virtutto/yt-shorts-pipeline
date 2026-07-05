import os
import tempfile
from pathlib import Path
from openai import OpenAI
from src.scrape_reddit import fetch_post
from src.rewrite_script import rewrite_story
from src.generate_audio import generate_tts
from src.assemble_video import assemble
from src.upload_youtube import upload
import asyncio

BROLL_DIR = str(Path(__file__).parent.parent / "assets" / "broll")


def _generate_fallback_post() -> dict:
    print("  Generating AI story as fallback...")
    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": (
                "Write a short Reddit-style story (200-300 words) that would be perfect for a YouTube Shorts video. "
                "It should be interesting, conversational, and sound like a real personal story. "
                "Respond with just the story text, no title."
            ),
        }],
    )
    story = resp.choices[0].message.content.strip()
    title = story.split(".")[0] if "." in story else story[:80]
    return {
        "title": title[:100],
        "selftext": story[:2000],
        "subreddit": "AskReddit",
        "permalink": "https://reddit.com/r/AskReddit",
        "post_id": "ai_fallback",
    }


async def main():
    print("[1/5] Scraping Reddit...")
    post = fetch_post()
    if not post:
        print("  Reddit unavailable, using AI-generated story")
        post = _generate_fallback_post()

    print(f"[2/5] Rewriting script for: {post['title']}")
    script = rewrite_story(post)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = f"{tmp}/audio.mp3"
        print("[3/5] Generating TTS...")
        await generate_tts(script, audio_path)

        video_path = f"{tmp}/output.mp4"
        print("[4/5] Assembling video...")
        assemble(script, audio_path, BROLL_DIR, video_path)

        print("[5/5] Uploading to YouTube...")
        url = upload(video_path, post)
        print(f"DONE: {url}")


if __name__ == "__main__":
    asyncio.run(main())
