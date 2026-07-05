import os
import tempfile
from pathlib import Path
from openai import OpenAI
from src.scrape_reddit import fetch_post
from src.rewrite_script import rewrite_story
from src.generate_audio import generate_tts
from src.assemble_video import assemble
from src.upload_youtube import upload
from src.dedup import is_seen, mark_seen

BROLL_DIR = str(Path(__file__).parent.parent / "assets" / "broll")

_TOPICS = [
    None,
    "Topic: a funny misunderstanding with a stranger.",
    "Topic: an unexpected act of kindness.",
    "Topic: something that happened at work.",
    "Topic: a childhood memory that still makes you laugh.",
    "Topic: a wild encounter with an animal.",
    "Topic: a travel story that went wrong.",
    "Topic: a coincidence that seemed impossible.",
    "Topic: an embarrassing moment in public.",
    "Topic: a story about a family tradition.",
]


def _generate_fallback_post(seed: int = 0) -> dict:
    topic = _TOPICS[seed % len(_TOPICS)]
    print(f"  Generating AI story as fallback (seed {seed})..." + (f" {topic}" if topic else ""))
    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    prompt = (
        "Write a short Reddit-style story (200-300 words) that would be perfect for a YouTube Shorts video. "
        "It should be interesting, conversational, and sound like a real personal story. "
        "Respond with just the story text, no title."
    )
    if topic:
        prompt += f" {topic}"
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
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


def main():
    print("[1/5] Scraping Reddit...")
    post = fetch_post()
    if not post:
        print("  Reddit unavailable, using AI-generated story")
        for attempt in range(10):
            post = _generate_fallback_post(attempt)
            if not is_seen(post["selftext"]):
                break
            print(f"  Story is a duplicate, retrying (attempt {attempt + 2})...")
        else:
            print("  Could not generate a unique story after 10 attempts, using last one anyway")

    print(f"[2/5] Rewriting script for: {post['title']}")
    script = rewrite_story(post)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = f"{tmp}/audio.mp3"
        print("[3/5] Generating TTS...")
        generate_tts(script, audio_path)

        video_path = f"{tmp}/output.mp4"
        print("[4/5] Assembling video...")
        assemble(script, audio_path, BROLL_DIR, video_path)

        print("[5/5] Uploading to YouTube...")
        url = upload(video_path, post)
        mark_seen(post["selftext"])
        print(f"DONE: {url}")


if __name__ == "__main__":
    main()
