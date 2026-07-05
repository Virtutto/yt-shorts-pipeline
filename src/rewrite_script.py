import os
from openai import OpenAI

SYSTEM_PROMPT = """You are a YouTube Shorts scriptwriter. Rewrite Reddit stories into 55-65 second scripts.
Rules:
- Start with a hook (first 3 seconds must grab attention)
- Keep natural conversational pacing
- End with a call to action: "What would you do? Comment below."
- Output only the script text, no labels or commentary"""

def rewrite_story(post: dict) -> str:
    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    prompt = f"Title: {post['title']}\n\nStory:\n{post['selftext']}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
