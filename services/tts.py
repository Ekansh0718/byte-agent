# services/tts.py
import requests
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

MURF_GENERATE_URL = "https://api.murf.ai/v1/speech/generate"

def speak(text: str, api_key: str, output_name: str = "stream_output.mp3") -> bytes:
    """
    Request Murf to synthesize `text` and return bytes of audio (mp3).
    This uses the Murf /generate endpoint and then downloads the audio file.
    """
    if not api_key:
        raise Exception("No Murf API key provided for TTS.")

    headers = {"Content-Type": "application/json", "api-key": api_key}
    payload = {
        "voiceId": "en-US-1",
        "text": text,
        "format": "mp3"
    }
    try:
        resp = requests.post(MURF_GENERATE_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        # Murf responds with 'audioFile' or similar. check keys:
        audio_url = j.get("audioUrl") or j.get("audioFile") or j.get("audio_url")
        if not audio_url:
            # some Murf plans return a task id; handle that flow if needed
            raise Exception("Murf did not return audio URL: " + str(j))

        # download audio
        r2 = requests.get(audio_url, timeout=30)
        r2.raise_for_status()
        audio_bytes = r2.content
        # save for debugging
        out_path = UPLOADS_DIR / output_name
        with open(out_path, "wb") as f:
            f.write(audio_bytes)
        return audio_bytes
    except Exception as e:
        logger.exception("Murf TTS failed")
        raise
