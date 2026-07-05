from gtts import gTTS

VOICE = "com"  # en-US via Google Translate

def generate_tts(script: str, output_path: str) -> list[dict]:
    tts = gTTS(script, lang="en", tld=VOICE, slow=False)
    tts.save(output_path)
    return []
