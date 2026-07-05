import edge_tts

VOICE = "en-US-GuyNeural"

async def generate_tts(script: str, output_path: str) -> list[dict]:
    communicate = edge_tts.Communicate(script, VOICE)
    words = []
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "offset": chunk["offset"] / 1e7,
                    "duration": chunk["duration"] / 1e7,
                })
    return words
