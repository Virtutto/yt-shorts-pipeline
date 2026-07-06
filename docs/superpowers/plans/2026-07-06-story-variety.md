# Story Variety Improvement Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make posted stories noticeably more varied day-to-day with 100+ diverse topics and multi-attribute prompt system.

**Architecture:** Modify `src/main.py` (topic list, prompt builder, generation loop) and `src/dedup.py` (threshold) — no new files or dependencies.

**Tech Stack:** Python 3.11+, Groq API (llama-3.3-70b-versatile), standard library `random`

## Global Constraints

- Zero new dependencies — standard library only
- `is_seen` check must happen immediately on candidate selection (not after upload)
- GitHub Actions cron schedule untouched (10, 16, 22 UTC)
- Existing `story_hashes.json` cache in GH Actions carries over transparently

---

### Task 1: Raise dedup threshold

**Files:**
- Modify: `src/dedup.py:7`

- [ ] **Change SIMILARITY_THRESHOLD to 0.45**

```python
SIMILARITY_THRESHOLD = 0.45
```

- [ ] **Commit**

```bash
git add src/dedup.py
git commit -m "chore: raise Jaccard dedup threshold from 0.25 to 0.45"
```

---

### Task 2: Replace topics, add attribute system, randomize seeds, shuffle, 30 attempts

**Files:**
- Modify: `src/main.py`

**Changes:**
1. Replace `_TOPICS` list with 100 diverse prompts (no `None` slot)
2. Add `_TONES`, `_SETTINGS`, `_CHARACTERS` constant lists
3. Rewrite `_generate_ai_post` to: accept no seed param, pick random topic + random attributes, use random Groq seed
4. Update `main()` to: shuffle topics, loop 30 attempts, pass attempt index for topic selection

- [ ] **Rewrite `src/main.py`**

```python
import os
import asyncio
import random
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
    "Topic: the worst roommate you ever had.",
    "Topic: a time you got lost in a strange city.",
    "Topic: a job interview that went off the rails.",
    "Topic: the most ridiculous rule you had to follow.",
    "Topic: a time you completely misjudged someone.",
    "Topic: something you believed as a kid that was hilariously wrong.",
    "Topic: a time your gut feeling saved you.",
    "Topic: the most awkward silence you've ever experienced.",
    "Topic: a time you had to pretend you knew what you were doing.",
    "Topic: the best piece of advice you never took.",
    "Topic: a text message you regret sending.",
    "Topic: meeting your partner's family for the first time.",
    "Topic: an ex you're glad got away.",
    "Topic: the worst wedding you've ever attended.",
    "Topic: a date that started great and ended terribly.",
    "Topic: the best relationship advice you ever got.",
    "Topic: a friend who turned out to be totally different than you thought.",
    "Topic: a family secret that came out at a dinner table.",
    "Topic: the most awkward family gathering you've been to.",
    "Topic: something your parents did that embarrassed you as a kid.",
    "Topic: a dream that predicted the future.",
    "Topic: the time you felt someone watching you when no one was there.",
    "Topic: an old house with a secret room.",
    "Topic: a noise at night that you never found the source of.",
    "Topic: a phone call that gave you chills.",
    "Topic: the creepiest thing a child has ever said to you.",
    "Topic: a coincidence that made you question reality.",
    "Topic: something you saw out of the corner of your eye that wasn't there.",
    "Topic: an abandoned place you explored.",
    "Topic: a message that came at exactly the wrong moment.",
    "Topic: a misheard lyric that changed everything for you.",
    "Topic: the worst haircut you ever got.",
    "Topic: a case of mistaken identity.",
    "Topic: a time you laughed at completely the wrong moment.",
    "Topic: the most embarrassing thing your phone did in public.",
    "Topic: a prank that went too far.",
    "Topic: an auto-correct disaster.",
    "Topic: a time you waved at someone who wasn't waving at you.",
    "Topic: the most awkward elevator ride of your life.",
    "Topic: a food disaster that ruined a special occasion.",
    "Topic: a random act of kindness you witnessed.",
    "Topic: the best compliment a stranger ever gave you.",
    "Topic: a moment that restored your faith in humanity.",
    "Topic: something a teacher did that changed your life.",
    "Topic: a time someone believed in you when you didn't believe in yourself.",
    "Topic: the most generous thing anyone has ever done for you.",
    "Topic: a small gesture that meant the world to you.",
    "Topic: a time a stranger helped you in an unexpected way.",
    "Topic: a thank-you note you'll never forget receiving.",
    "Topic: a pet that chose you.",
    "Topic: something your pet did that seemed almost human.",
    "Topic: the joy of adopting an older animal.",
    "Topic: a moment you connected with an animal in a surprising way.",
    "Topic: the incredible journey of a rescue animal.",
    "Topic: a time travel story that actually made sense.",
    "Topic: a time your skill impressed everyone.",
    "Topic: the day you met your idol.",
    "Topic: a contest you entered not expecting to win.",
    "Topic: the most surprising outcome of a dare.",
    "Topic: a time you found something priceless in a thrift store.",
    "Topic: a vacation that changed your perspective on life.",
    "Topic: a road trip that went completely off course.",
    "Topic: the worst hotel experience you've ever had.",
    "Topic: a travel scam you almost fell for.",
    "Topic: a local tradition that shocked an outsider.",
    "Topic: the most beautiful place you've ever been.",
    "Topic: a train or bus ride you'll never forget.",
    "Topic: a language barrier that led to a funny situation.",
    "Topic: a crash course in adulthood you weren't ready for.",
    "Topic: the biggest financial mistake you ever made.",
    "Topic: a time you had to adult harder than ever before.",
    "Topic: learning a skill the hard way.",
    "Topic: the best decision you made on impulse.",
    "Topic: a moment you realized you had become your parent.",
    "Topic: the most satisfying thing you ever accomplished.",
    "Topic: the most scared you've ever been.",
    "Topic: a time you thought you were going to die but survived.",
    "Topic: a panic moment that you somehow handled.",
    "Topic: the bravest thing you've ever seen someone do.",
    "Topic: a time you faced your biggest fear.",
    "Topic: a close call that still haunts you.",
    "Topic: a situation that got way out of hand before you fixed it.",
    "Topic: the most stressful day of your life.",
    "Topic: the stupidest thing you did that somehow worked out.",
    "Topic: a lesson you had to learn more than once.",
    "Topic: a time you accidentally broke something important.",
    "Topic: the worst customer service experience you've had.",
    "Topic: a time you had to deal with a difficult person.",
    "Topic: the most bizarre conversation you've overheard.",
    "Topic: a workplace prank war that got out of control.",
    "Topic: the strangest customer you ever served.",
    "Topic: a coworker mystery that was never solved.",
    "Topic: the worst job you ever quit.",
    "Topic: a time you cried at work and how it turned out.",
    "Topic: the most unethical thing a boss asked you to do.",
    "Topic: a time you stood up for yourself and it paid off.",
    "Topic: an argument you had that completely changed your mind.",
    "Topic: a time you walked away from something toxic.",
    "Topic: the hardest goodbye you ever had to say.",
    "Topic: a moment you chose kindness over being right.",
    "Topic: the most painful truth someone ever told you.",
    "Topic: a time you forgave someone who didn't deserve it.",
    "Topic: the best revenge that wasn't really revenge.",
    "Topic: a mistake that taught you more than success ever could.",
    "Topic: a moment you realized social media is not real life.",
    "Topic: the most out-of-touch thing someone rich said to you.",
    "Topic: a generational culture clash you experienced.",
    "Topic: the weirdest subculture you've ever encountered.",
]

_TONES = ["funny", "suspenseful", "heartwarming", "bittersweet"]
_SETTINGS = ["at work", "at school", "at home", "while traveling"]
_CHARACTERS = ["a stranger", "a friend", "a family member", "a pet"]


def _generate_ai_post(topic_num: int, topic_list: list[str]) -> dict:
    topic = topic_list[topic_num % len(topic_list)]
    tone = random.choice(_TONES)
    setting = random.choice(_SETTINGS)
    character = random.choice(_CHARACTERS)
    groq_seed = random.randint(0, 2**31 - 1)

    print(f"  Generating AI story (topic {topic_num}, tone={tone}, setting={setting}, character={character}, seed={groq_seed})")
    print(f"    {topic}")

    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    prompt = (
        "Write a short Reddit-style story (200-300 words) that would be perfect for a YouTube Shorts video. "
        "It should be interesting, conversational, and sound like a real personal story. "
        "Respond with just the story text, no title. "
        f"Here is the topic: {topic} "
        f"Tell it in a {tone} tone, set {setting}, involving {character}."
    )
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        seed=groq_seed,
        temperature=0.9,
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
    print("[1/5] Generating story...")
    post = None

    shuffled = _TOPICS.copy()
    random.shuffle(shuffled)
    offset = random.randrange(0, len(shuffled))

    for attempt in range(30):
        topic_idx = (offset + attempt) % len(shuffled)
        candidate = _generate_ai_post(topic_idx, shuffled)
        if not is_seen(candidate["selftext"]):
            post = candidate
            mark_seen(post["selftext"])
            break
        print(f"  Story is a duplicate, retrying (attempt {attempt + 2})...")

    if not post:
        print("  AI exhausted, trying Reddit...")
        post = fetch_post()
    if not post:
        print("  All sources empty, using AI anyway")
        shuffled = _TOPICS.copy()
        random.shuffle(shuffled)
        post = _generate_ai_post(0, shuffled)
        mark_seen(post["selftext"])

    print(f"[2/5] Rewriting script for: {post['title']}")
    script = rewrite_story(post)

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = f"{tmp}/audio.mp3"
        print("[3/5] Generating TTS...")
        word_timings = await generate_tts(script, audio_path)

        video_path = f"{tmp}/output.mp4"
        print("[4/5] Assembling video...")
        assemble(script, audio_path, BROLL_DIR, video_path, word_timings)

        print("[5/5] Uploading to YouTube...")
        url = upload(video_path, post)
        print(f"DONE: {url}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Commit**

```bash
git add src/main.py
git commit -m "feat: expand to 100 topics with multi-attribute prompt system"
```

---

### Task 3: Verify pipeline still works

- [ ] **Run a dry check**

```bash
cd C:\Users\adamd\yt-shorts-pipeline
python -c "from src.dedup import is_seen, mark_seen; print('dedup OK'); from src.main import _TOPICS, _TONES, _SETTINGS, _CHARACTERS; print(f'topics={len(_TOPICS)}, tones={len(_TONES)}, settings={len(_SETTINGS)}, chars={len(_CHARACTERS)}')"
```

Expected output: `dedup OK` and `topics=100, tones=4, settings=4, chars=4`

- [ ] **Check git status is clean**

```bash
git status
```
Expected: clean working tree, everything committed

- [ ] **Push to GitHub**

```bash
git push origin master
```
