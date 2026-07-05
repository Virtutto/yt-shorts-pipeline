import tempfile
from pathlib import Path
from src.scrape_reddit import fetch_post
from src.rewrite_script import rewrite_story
from src.generate_audio import generate_tts
from src.assemble_video import assemble
from src.upload_youtube import upload
import asyncio

BROLL_DIR = str(Path(__file__).parent.parent / "assets" / "broll")

async def main():
    print("[1/5] Scraping Reddit...")
    post = fetch_post()
    if not post:
        print("No suitable post found")
        return

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
