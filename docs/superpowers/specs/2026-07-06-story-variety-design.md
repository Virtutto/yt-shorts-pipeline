# Story Variety Improvement Design

## Problem

The YouTube Shorts pipeline posts stories that are too similar across runs because:

1. **Fixed Groq seed** (`seed=attempt+42`) makes each attempt number produce the exact same deterministic story every pipeline run
2. **Only 20 topics** with a wasted `None` slot at index 0
3. **Only 10 attempts** per run — half the topic space never tried
4. **Jaccard threshold 0.25** is too low — stories on similar topics falsely dedup each other
5. **No prompt structure variety** — every story follows the same narrative pattern

## Solution: Approach B — Smart Generation with Multi-Attribute Prompts

### 1. Topic Expansion (20 → ~100)

Replace the 20 topics with 100 diverse prompts spanning genres:
- Life events (30): roommate stories, getting lost, job interviews gone wrong, etc.
- Relationships (20): regretful texts, meeting families, exes, etc.
- Supernatural/creepy (15): prophetic dreams, being watched, secret rooms, etc.
- Funny/awkward (20): misheard lyrics, bad haircuts, mistaken identity, etc.
- Wholesome (15): random kindness, best compliments, faith in humanity, etc.

No `None` topic — every slot has a real prompt.

### 2. Multi-Attribute Prompt System

Each generation randomly combines:
- **Tone**: funny, suspenseful, heartwarming, bittersweet
- **Setting**: at work, at school, at home, while traveling
- **Character**: a stranger, a friend, a family member, a pet

Combined: 100 topics × 4 tones × 4 settings × 4 characters = 6,400 unique combinations.

Prompt template:
```
Write a short Reddit-style story (200-300 words)...
Here is the topic: [TOPIC].
Tell it in a [TONE] tone, set [SETTING], involving [CHARACTER].
```

### 3. Seed Randomization

Replace `seed=attempt+42` with `random.randint(0, 2**31-1)` per generation call so every call is fresh.

### 4. Topic Shuffling

Before the attempt loop, shuffle all 100 topics into random order. Each attempt picks `topics[attempt % 100]`. Add a random starting offset so runs don't always start at index 0.

### 5. Jaccard Threshold

Raise `SIMILARITY_THRESHOLD` from 0.25 → 0.45 to reduce false dedup.

### 6. Attempts

Increase from 10 → 30 per run.

## Files Changed

| File | Change |
|---|---|
| `src/main.py` | New 100-topic list, attribute system, random seeds, topic shuffle, 30 attempts, `is_seen` immediately on candidate |
| `src/dedup.py` | `SIMILARITY_THRESHOLD` 0.25 → 0.45 |

## No New Dependencies

All changes use standard library (`random`, existing OpenAI/Groq client).

## Verification

After implementation, run the pipeline locally once to verify:
- Stories are generated with varied tones, settings, and characters
- No two consecutive runs produce the same story
- Dedup correctly catches true duplicates (if any)
