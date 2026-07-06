import os
import edge_tts
from edge_tts import exceptions

VOICE = "en-US-JennyNeural"


async def generate_tts(script: str, output_path: str) -> list[dict]:
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
    communicate = edge_tts.Communicate(script, VOICE, proxy=proxy, boundary="WordBoundary")
    words = []
    try:
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
    except (exceptions.WebSocketError, exceptions.NoAudioReceived) as e:
        proxy_hint = " Set HTTPS_PROXY env var" if not proxy else " Check your proxy"
        raise RuntimeError(
            f"edge-tts failed: {e}.{proxy_hint} or try running locally instead of GitHub Actions."
        ) from e
    return words
